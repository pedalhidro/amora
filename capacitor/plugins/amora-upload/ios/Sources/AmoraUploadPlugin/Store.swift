import Foundation

/// Estado durável do envio — o MESMO modelo do Store.java (contrato em
/// docs/PLAN-native-upload.md §3): arquivos escolhidos (picks/), pedaços
/// gerados pelo JS (blobs/), corpos multipart prontos (jobs/<id>/body.bin —
/// sessão em segundo plano só sobe de arquivo) e o manifesto dos jobs.
///
/// Mora em Application Support (o SO não apaga, ao contrário de Caches), fora
/// do backup do iCloud. Tudo passa por uma fila serial.
///
/// Diferença pro Android: no iOS a transferência em segundo plano SOBREVIVE à
/// morte do app — um job "sending" no boot pode ter uma task viva na sessão.
/// Quem decide (re-cria a task ou espera) é o UploadQueue, ao reconciliar com
/// `getAllTasks`.
final class Store {

    static let keepFinal: TimeInterval = 7 * 24 * 3600     // job final sem ack
    static let keepOrphan: TimeInterval = 7 * 24 * 3600    // pick/blob sem job
    static let giveUp: TimeInterval = 24 * 3600            // desiste de re-tentar
    static let backoff: [TimeInterval] = [30, 120, 600, 1800, 3600]

    static let shared = Store()

    let root: URL, picks: URL, blobs: URL, bodies: URL
    private let manifest: URL
    private let q = DispatchQueue(label: "co.pedalhidrografi.amora.upload.store")
    private var jobs: [String: [String: Any]] = [:]
    var onChange: (([String: Any]) -> Void)?

    private init() {
        let fm = FileManager.default
        let base = (try? fm.url(for: .applicationSupportDirectory, in: .userDomainMask, appropriateFor: nil, create: true))
            ?? fm.temporaryDirectory
        root = base.appendingPathComponent("amora-upload", isDirectory: true)
        picks = root.appendingPathComponent("picks", isDirectory: true)
        blobs = root.appendingPathComponent("blobs", isDirectory: true)
        bodies = root.appendingPathComponent("jobs", isDirectory: true)
        manifest = root.appendingPathComponent("manifest.json")
        for d in [root, picks, blobs, bodies] { try? fm.createDirectory(at: d, withIntermediateDirectories: true) }
        var r = root
        var rv = URLResourceValues()
        rv.isExcludedFromBackup = true
        try? r.setResourceValues(rv)
        jobs = load()
    }

    // MARK: Manifesto

    private func load() -> [String: [String: Any]] {
        guard let data = try? Data(contentsOf: manifest),
              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let j = obj["jobs"] as? [String: [String: Any]] else { return [:] }
        return j
    }

    private func save() {
        guard let data = try? JSONSerialization.data(withJSONObject: ["jobs": jobs]) else { return }
        try? data.write(to: manifest, options: .atomic)
    }

    private func changed(_ id: String, persist: Bool = true) {
        if persist { save() }
        guard let j = jobs[id] else { return }
        let pub = Store.publicView(j)
        onChange?(pub)
    }

    /// O que o JS vê: sem a especificação do request.
    static func publicView(_ j: [String: Any]) -> [String: Any] {
        var p: [String: Any] = [:]
        for k in ["jobId", "meta", "state", "attempts", "sent", "total", "nextAttemptAt",
                  "httpStatus", "response", "error", "createdAt", "updatedAt"] {
            if let v = j[k] { p[k] = v }
        }
        return p
    }

    static func nowMs() -> Double { Date().timeIntervalSince1970 * 1000 }

    // MARK: Jobs

    func createJob(_ spec: [String: Any]) -> [String: Any] {
        q.sync {
            let id = spec["jobId"] as? String ?? ""
            if let existing = jobs[id] { return Store.publicView(existing) }
            var j = spec
            let now = Store.nowMs()
            j["state"] = "queued"
            j["attempts"] = 0
            j["createdAt"] = now
            j["updatedAt"] = now
            jobs[id] = j
            changed(id)
            return Store.publicView(j)
        }
    }

    func snapshot(_ id: String) -> [String: Any]? { q.sync { jobs[id] } }
    func listPublic() -> [[String: Any]] { q.sync { jobs.values.map(Store.publicView) } }
    func allIds() -> [String] { q.sync { Array(jobs.keys) } }

    /// Jobs que precisam de uma task (queued/waiting/sending), com o predecessor
    /// `after` concluído. Predecessor falho → este falha junto. Velho demais → falha.
    func runnable() -> [String] {
        q.sync {
            var out: [String] = []
            let now = Store.nowMs()
            let ids = jobs.keys.sorted { (jobs[$0]?["createdAt"] as? Double ?? 0) < (jobs[$1]?["createdAt"] as? Double ?? 0) }
            for id in ids {
                guard let j = jobs[id], let st = j["state"] as? String,
                      st == "queued" || st == "waiting" || st == "sending" else { continue }
                if let after = j["after"] as? String, !after.isEmpty {
                    let ps = jobs[after]?["state"] as? String ?? "done"   // ack'ado = concluído
                    if ps == "failed" { finishLocked(id, "failed", 0, nil, "o envio anterior desta cadeia falhou"); continue }
                    if ps != "done" { continue }
                }
                if now - (j["createdAt"] as? Double ?? now) > Store.giveUp * 1000 {
                    finishLocked(id, "failed", j["httpStatus"] as? Int ?? 0, nil,
                                 "desisti depois de 24 h tentando" + ((j["error"] as? String).map { " — \($0)" } ?? ""))
                    continue
                }
                out.append(id)
            }
            return out
        }
    }

    /// A task do job começou (ou foi criada): conta a tentativa.
    func markSending(_ id: String) {
        q.sync {
            guard var j = jobs[id] else { return }
            j["state"] = "sending"
            j["attempts"] = (j["attempts"] as? Int ?? 0) + 1
            j["updatedAt"] = Store.nowMs()
            j["nextAttemptAt"] = nil
            jobs[id] = j
            changed(id)
        }
    }

    func progress(_ id: String, sent: Int64, total: Int64) {
        q.sync {
            guard var j = jobs[id], j["state"] as? String == "sending" else { return }
            j["sent"] = sent
            j["total"] = total
            jobs[id] = j
            changed(id, persist: false)   // progresso não vai pro disco
        }
    }

    func done(_ id: String, status: Int, response: Any?) {
        q.sync { finishLocked(id, "done", status, response, nil) }
    }

    func failed(_ id: String, status: Int, response: Any?, error: String) {
        q.sync { finishLocked(id, "failed", status, response, error) }
    }

    /// Falha transitória: devolve o instante da próxima tentativa.
    func retryLater(_ id: String, status: Int, error: String) -> Date {
        q.sync {
            guard var j = jobs[id] else { return Date() }
            let attempts = max(1, j["attempts"] as? Int ?? 1)
            let delay = Store.backoff[min(attempts - 1, Store.backoff.count - 1)]
            let next = Date().addingTimeInterval(delay)
            j["state"] = "waiting"
            j["nextAttemptAt"] = next.timeIntervalSince1970 * 1000
            j["httpStatus"] = status > 0 ? status : nil
            j["error"] = error
            j["updatedAt"] = Store.nowMs()
            j["sent"] = nil
            j["total"] = nil
            jobs[id] = j
            changed(id)
            return next
        }
    }

    private func finishLocked(_ id: String, _ state: String, _ status: Int, _ response: Any?, _ error: String?) {
        guard var j = jobs[id] else { return }
        j["state"] = state
        if status > 0 { j["httpStatus"] = status }
        if let r = response { j["response"] = r }
        j["error"] = error
        j["updatedAt"] = Store.nowMs()
        j["nextAttemptAt"] = nil
        j["sent"] = nil
        j["total"] = nil
        jobs[id] = j
        changed(id)
        // O corpo pronto só serve pra re-tentar: estado final → some.
        try? FileManager.default.removeItem(at: bodies.appendingPathComponent(id, isDirectory: true))
    }

    func cancel(_ id: String) -> Bool {
        q.sync {
            guard let st = jobs[id]?["state"] as? String, st != "done", st != "failed" else { return false }
            finishLocked(id, "failed", 0, nil, "cancelled")
            return true
        }
    }

    /// ↻ do JS num job que falhou: volta pra fila do zero.
    func retry(_ id: String) -> Bool {
        q.sync {
            guard var j = jobs[id], j["state"] as? String == "failed" else { return false }
            let now = Store.nowMs()
            j["state"] = "queued"
            j["attempts"] = 0
            j["createdAt"] = now
            j["updatedAt"] = now
            for k in ["error", "httpStatus", "response", "nextAttemptAt", "sent", "total"] { j[k] = nil }
            jobs[id] = j
            changed(id)
            return true
        }
    }

    func state(_ id: String) -> String? { q.sync { jobs[id]?["state"] as? String } }

    /// O JS registrou o resultado: some o job e os arquivos que só ele usava.
    func ack(_ id: String) {
        q.sync {
            guard let j = jobs[id], let st = j["state"] as? String, st == "done" || st == "failed" else { return }
            jobs[id] = nil
            deleteUnreferencedLocked(Store.sources(of: j))
            try? FileManager.default.removeItem(at: bodies.appendingPathComponent(id, isDirectory: true))
            save()
        }
    }

    func release(_ pickIds: [String]) {
        q.sync { deleteUnreferencedLocked(Set(pickIds.map { "pick:\($0)" })) }
    }

    private static func sources(of job: [String: Any]) -> Set<String> {
        var s = Set<String>()
        for f in job["files"] as? [[String: Any]] ?? [] {
            guard let src = f["source"] as? [String: Any] else { continue }
            if let p = src["pickId"] as? String { s.insert("pick:\(p)") }
            if let b = src["blobId"] as? String { s.insert("blob:\(b)") }
        }
        return s
    }

    private func deleteUnreferencedLocked(_ candidates: Set<String>) {
        var live = Set<String>()
        for j in jobs.values { live.formUnion(Store.sources(of: j)) }
        for c in candidates where !live.contains(c) {
            let id = String(c.dropFirst(5))
            if let f = c.hasPrefix("pick:") ? findPick(id) : blobFile(id) { try? FileManager.default.removeItem(at: f) }
        }
    }

    // MARK: Arquivos

    static func validId(_ id: String?) -> Bool {
        guard let id = id, !id.isEmpty, id.count <= 64 else { return false }
        return id.range(of: "^[A-Za-z0-9-]+$", options: .regularExpression) != nil
    }

    func blobFile(_ id: String) -> URL? { Store.validId(id) ? blobs.appendingPathComponent(id) : nil }

    func findPick(_ id: String) -> URL? {
        guard Store.validId(id),
              let names = try? FileManager.default.contentsOfDirectory(atPath: picks.path) else { return nil }
        guard let name = names.first(where: { $0 == id || $0.hasPrefix(id + ".") }) else { return nil }
        return picks.appendingPathComponent(name)
    }

    func sourceFile(_ source: [String: Any]?) -> URL? {
        guard let s = source else { return nil }
        if let p = s["pickId"] as? String { return findPick(p) }
        if let b = s["blobId"] as? String { return blobFile(b) }
        return nil
    }

    func bodyFile(_ id: String) -> URL {
        bodies.appendingPathComponent(id, isDirectory: true).appendingPathComponent("body.bin")
    }

    /// Varredura (no load do plugin): jobs finais velhos e arquivos órfãos velhos.
    func sweep() {
        q.sync {
            let now = Store.nowMs()
            var dirty = false
            for (id, j) in jobs {
                let st = j["state"] as? String
                if (st == "done" || st == "failed"), now - (j["updatedAt"] as? Double ?? now) > Store.keepFinal * 1000 {
                    jobs[id] = nil
                    dirty = true
                }
            }
            if dirty { save() }
            var live = Set<String>()
            for j in jobs.values { live.formUnion(Store.sources(of: j)) }
            let fm = FileManager.default
            for (dir, prefix) in [(picks, "pick:"), (blobs, "blob:")] {
                for name in (try? fm.contentsOfDirectory(atPath: dir.path)) ?? [] {
                    let id = name.split(separator: ".").first.map(String.init) ?? name
                    if live.contains(prefix + id) { continue }
                    let url = dir.appendingPathComponent(name)
                    let mod = (try? fm.attributesOfItem(atPath: url.path)[.modificationDate] as? Date) ?? Date()
                    if Date().timeIntervalSince(mod) > Store.keepOrphan { try? fm.removeItem(at: url) }
                }
            }
            for name in (try? fm.contentsOfDirectory(atPath: bodies.path)) ?? [] where jobs[name] == nil {
                try? fm.removeItem(at: bodies.appendingPathComponent(name))
            }
        }
    }
}
