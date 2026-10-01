import Foundation

/// A fila de envio do iOS: uma URLSession em SEGUNDO PLANO. O sistema sobe os
/// arquivos com o app suspenso ou morto e relança o app (em segundo plano)
/// pra entregar o resultado — por isso o AppDelegate encaminha
/// `handleEventsForBackgroundURLSession` pra cá (patch no run-ios.sh).
///
/// Cada job vira UMA upload task, de arquivo (`jobs/<id>/body.bin`, o
/// multipart pronto — sessão em segundo plano não aceita corpo em memória).
/// Recuo de falha transitória = nova task com `earliestBeginDate`: quem
/// agenda é o sistema, então funciona com o app morto. Política (recuos, 24 h,
/// o que é transitório) = a do Store, igual ao Android.
public final class AmoraUploadQueue: NSObject, URLSessionDataDelegate {

    public static let shared = AmoraUploadQueue()
    static let sessionId = "co.pedalhidrografi.amora.upload"

    private let store = Store.shared
    private var responses: [Int: Data] = [:]   // taskIdentifier → corpo da resposta
    private var completion: (() -> Void)?
    private let delegateQueue: OperationQueue = {
        let q = OperationQueue()
        q.maxConcurrentOperationCount = 1
        return q
    }()

    private lazy var session: URLSession = {
        let c = URLSessionConfiguration.background(withIdentifier: AmoraUploadQueue.sessionId)
        c.sessionSendsLaunchEvents = true
        c.isDiscretionary = false
        c.allowsCellularAccess = true
        c.httpMaximumConnectionsPerHost = 2
        c.timeoutIntervalForResource = 24 * 3600
        return URLSession(configuration: c, delegate: self, delegateQueue: delegateQueue)
    }()

    static let userAgent: String = {
        let v = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "?"
        let os = ProcessInfo.processInfo.operatingSystemVersion
        return "Amora-iOS/\(v) (iOS \(os.majorVersion).\(os.minorVersion))"
    }()

    /// Do AppDelegate — `application(_:handleEventsForBackgroundURLSession:completionHandler:)`.
    public func handleEvents(identifier: String, completionHandler: @escaping () -> Void) {
        guard identifier == AmoraUploadQueue.sessionId else { completionHandler(); return }
        completion = completionHandler
        _ = session   // recria a sessão com o mesmo id: os eventos chegam no delegate
    }

    public func urlSessionDidFinishEvents(forBackgroundURLSession session: URLSession) {
        DispatchQueue.main.async {
            let c = self.completion
            self.completion = nil
            c?()
        }
    }

    /// Garante uma task pra cada job que precisa de uma (boot, enqueue, retry,
    /// predecessor concluído). Idempotente: job com task viva é deixado em paz.
    func pump() {
        session.getAllTasks { tasks in
            let live = Set(tasks.compactMap { t -> String? in
                t.state == .running || t.state == .suspended ? t.taskDescription : nil
            })
            for id in self.store.runnable() where !live.contains(id) { self.start(id) }
        }
    }

    func cancel(_ id: String) {
        session.getAllTasks { tasks in
            for t in tasks where t.taskDescription == id { t.cancel() }
        }
    }

    private func start(_ id: String) {
        guard let job = store.snapshot(id),
              let urlString = job["url"] as? String, let url = URL(string: urlString) else { return }
        let body = store.bodyFile(id)
        let boundary = "----AmoraBoundary" + id
        do {
            if !FileManager.default.fileExists(atPath: body.path) {
                try Multipart.write(job: job, store: store, boundary: boundary, to: body)
            }
        } catch {
            store.failed(id, status: 0, response: nil, error: "montando o envio: \(error.localizedDescription)")
            return
        }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        req.setValue("application/json", forHTTPHeaderField: "Accept")
        req.setValue(AmoraUploadQueue.userAgent, forHTTPHeaderField: "User-Agent")
        let task = session.uploadTask(with: req, fromFile: body)
        task.taskDescription = id
        let next = (job["nextAttemptAt"] as? Double).map { Date(timeIntervalSince1970: $0 / 1000) }
        if let next = next, next > Date() {
            task.earliestBeginDate = next   // segue "waiting" até o sistema começar
        } else {
            store.markSending(id)
        }
        task.resume()
    }

    // MARK: URLSessionDataDelegate

    public func urlSession(_ session: URLSession, task: URLSessionTask, didSendBodyData bytesSent: Int64,
                           totalBytesSent: Int64, totalBytesExpectedToSend: Int64) {
        guard let id = task.taskDescription else { return }
        let st = store.state(id)
        if st == "waiting" || st == "queued" { store.markSending(id) }
        store.progress(id, sent: totalBytesSent, total: totalBytesExpectedToSend)
    }

    public func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        responses[dataTask.taskIdentifier, default: Data()].append(data)
    }

    public func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        let data = responses.removeValue(forKey: task.taskIdentifier)
        guard let id = task.taskDescription else { return }
        let st = store.state(id)
        guard st == "sending" || st == "waiting" || st == "queued" else { pump(); return }   // cancelado/ack'ado
        let status = (task.response as? HTTPURLResponse)?.statusCode ?? 0
        let body = AmoraUploadQueue.parse(data)
        if let error = error as NSError? {
            if error.code == NSURLErrorCancelled { return }
            _ = store.retryLater(id, status: 0, error: error.localizedDescription)
        } else if (200..<300).contains(status) {
            store.done(id, status: status, response: body)
        } else if status == 408 || status == 429 || status >= 500 {
            _ = store.retryLater(id, status: status, error: AmoraUploadQueue.errorText(body, status))
        } else {
            store.failed(id, status: status, response: body, error: AmoraUploadQueue.errorText(body, status))
        }
        pump()   // re-tentativa agendada, ou o próximo de uma cadeia
    }

    // MARK: Resposta

    static func parse(_ data: Data?) -> Any? {
        guard let data = data, !data.isEmpty else { return nil }
        if let obj = try? JSONSerialization.jsonObject(with: data), obj is [String: Any] { return obj }
        // Ex.: página HTML de bloqueio da Cloudflare — guarda o começo pro diagnóstico.
        let text = String(decoding: data.prefix(300), as: UTF8.self)
        return ["raw": text]
    }

    /// Mesma leitura que o postMedia do subir.html: details, senão error, senão HTTP n.
    static func errorText(_ body: Any?, _ status: Int) -> String {
        if let b = body as? [String: Any] {
            if let d = b["details"] as? [Any], !d.isEmpty { return d.map { "\($0)" }.joined(separator: "; ") }
            if let e = b["error"] as? String { return e }
        }
        return "HTTP \(status)"
    }
}

/// O corpo multipart/form-data escrito em ARQUIVO, em fluxo (nada inteiro na
/// memória) — mesmo formato do FormData do subir.html e do Uploader.java.
enum Multipart {
    static func quote(_ s: String) -> String {
        s.replacingOccurrences(of: "\"", with: "%22")
            .replacingOccurrences(of: "\r", with: "%0D")
            .replacingOccurrences(of: "\n", with: "%0A")
    }

    static func write(job: [String: Any], store: Store, boundary: String, to dest: URL) throws {
        let fm = FileManager.default
        try fm.createDirectory(at: dest.deletingLastPathComponent(), withIntermediateDirectories: true)
        let tmp = dest.appendingPathExtension("tmp")
        fm.createFile(atPath: tmp.path, contents: nil)
        let out = try FileHandle(forWritingTo: tmp)
        defer { try? out.close() }
        func put(_ s: String) { out.write(Data(s.utf8)) }
        for (k, v) in job["fields"] as? [String: Any] ?? [:] {
            put("--\(boundary)\r\nContent-Disposition: form-data; name=\"\(quote(k))\"\r\n\r\n\(v)\r\n")
        }
        for f in job["files"] as? [[String: Any]] ?? [] {
            guard let src = store.sourceFile(f["source"] as? [String: Any]), fm.fileExists(atPath: src.path) else {
                throw NSError(domain: "AmoraUpload", code: 1, userInfo: [NSLocalizedDescriptionKey:
                    "arquivo do envio sumiu do aparelho (\(f["field"] ?? "?"))"])
            }
            let field = f["field"] as? String ?? "file"
            let filename = f["filename"] as? String ?? "file"
            let ct = f["contentType"] as? String ?? "application/octet-stream"
            put("--\(boundary)\r\nContent-Disposition: form-data; name=\"\(quote(field))\"; filename=\"\(quote(filename))\"\r\nContent-Type: \(ct)\r\n\r\n")
            let input = try FileHandle(forReadingFrom: src)
            defer { try? input.close() }
            while true {
                let chunk = input.readData(ofLength: 1 << 20)
                if chunk.isEmpty { break }
                out.write(chunk)
            }
            put("\r\n")
        }
        put("--\(boundary)--\r\n")
        try? out.close()
        if fm.fileExists(atPath: dest.path) { try fm.removeItem(at: dest) }
        try fm.moveItem(at: tmp, to: dest)
    }
}
