import Foundation
import Capacitor
import ImageIO
import PhotosUI
import UniformTypeIdentifiers

/// Seletor nativo de mídia + envio em segundo plano — o MESMO contrato do
/// plugin Android (docs/PLAN-native-upload.md §3). O JS segue dono do produto
/// (hash, EXIF, variantes, TTL, álbum); aqui só (1) trazer o arquivo da
/// fototeca pro armazenamento do app SEM a espera que o seletor da web impõe
/// (o WebKit pede a versão "compatível" e o iOS transcodifica cada vídeo com o
/// seletor aberto e sem progresso), e (2) subir os POSTs montados pelo JS
/// numa URLSession em segundo plano.
@objc(AmoraUploadPlugin)
public class AmoraUploadPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "AmoraUploadPlugin"
    public let jsName = "AmoraUpload"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "info", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "pick", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "readChunk", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "putBlob", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "enqueue", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "listJobs", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "retry", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "cancel", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "ack", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "release", returnType: CAPPluginReturnPromise),
    ]

    static let apiVersion = 1
    static let maxChunk = 4 << 20

    private let store = Store.shared
    private let io = DispatchQueue(label: "co.pedalhidrografi.amora.upload.io", qos: .userInitiated)
    private let copyIo = DispatchQueue(label: "co.pedalhidrografi.amora.upload.copy", qos: .userInitiated)
    fileprivate var pickCall: CAPPluginCall?

    public override func load() {
        store.onChange = { [weak self] job in self?.notifyListeners("jobChanged", data: job) }
        io.async {
            self.store.sweep()
            AmoraUploadQueue.shared.pump()   // re-anexa a sessão e o que sobrou na fila
        }
    }

    @objc func info(_ call: CAPPluginCall) {
        call.resolve(["apiVersion": AmoraUploadPlugin.apiVersion, "platform": "ios", "picker": "phpicker"])
    }

    // MARK: pick

    @objc func pick(_ call: CAPPluginCall) {
        guard #available(iOS 14, *) else {
            call.reject("a galeria nativa precisa do iOS 14+")
            return
        }
        let videos = call.getBool("videos") ?? false
        let limit = call.getInt("limit") ?? 0
        DispatchQueue.main.async {
            // Sem `photoLibrary:` o seletor roda FORA do app e não pede
            // permissão nenhuma — o original vem com EXIF/GPS e o moov dos vídeos.
            var cfg = PHPickerConfiguration()
            cfg.filter = videos ? .any(of: [.images, .videos]) : .images
            cfg.selectionLimit = limit
            // .current: o arquivo como está na fototeca (o HEVC do vídeo, sem
            // transcodificar — era a espera do seletor da web).
            cfg.preferredAssetRepresentationMode = .current
            if #available(iOS 15, *) { cfg.selection = .ordered }
            let picker = PHPickerViewController(configuration: cfg)
            picker.delegate = self
            self.pickCall = call
            guard let vc = self.bridge?.viewController else {
                self.pickCall = nil
                call.reject("sem view controller")
                return
            }
            vc.present(picker, animated: true)
        }
    }

    @available(iOS 14, *)
    fileprivate func copyPicked(_ results: [PHPickerResult], _ call: CAPPluginCall) {
        let origin = pageOriginURL()
        copyIo.async {
            var items: [[String: Any]] = []
            var failed: [[String: Any]] = []
            for (i, r) in results.enumerated() {
                let p = r.itemProvider
                let video = p.hasItemConformingToTypeIdentifier(UTType.movie.identifier)
                // Foto: JPEG (o mesmo que o seletor da web entrega hoje — o
                // pipeline e a dedup por pHash ficam iguais); HEIC só se não houver.
                let type = video ? UTType.movie.identifier
                    : (p.hasItemConformingToTypeIdentifier(UTType.jpeg.identifier) ? UTType.jpeg.identifier : UTType.image.identifier)
                let base = p.suggestedName ?? (video ? "video" : "imagem")
                let sem = DispatchSemaphore(value: 0)
                var item: [String: Any]?
                var err: String?
                _ = p.loadFileRepresentation(forTypeIdentifier: type) { url, error in
                    defer { sem.signal() }
                    // O arquivo some quando este callback retorna: copia AQUI.
                    guard let url = url else { err = error?.localizedDescription ?? "sem arquivo"; return }
                    let ext = url.pathExtension.isEmpty ? (video ? "mov" : "jpg") : url.pathExtension.lowercased()
                    let pickId = UUID().uuidString.lowercased()
                    let dest = self.store.picks.appendingPathComponent("\(pickId).\(ext)")
                    do { try FileManager.default.copyItem(at: url, to: dest) } catch {
                        err = error.localizedDescription
                        return
                    }
                    let size = (try? FileManager.default.attributesOfItem(atPath: dest.path)[.size] as? NSNumber)?.intValue ?? 0
                    let mime = UTType(filenameExtension: ext)?.preferredMIMEType ?? (video ? "video/quicktime" : "image/jpeg")
                    var it: [String: Any] = [
                        "pickId": pickId, "kind": video ? "video" : "image",
                        "name": "\(base).\(ext)", "mime": mime, "size": size,
                    ]
                    if let u = self.fileURL(for: dest, origin: origin) { it["url"] = u }
                    var diag: [String: Any] = ["type": type]
                    if !video { diag["hasGps"] = AmoraUploadPlugin.hasGps(dest) }
                    it["diag"] = diag
                    item = it
                }
                sem.wait()
                if let it = item { items.append(it) } else { failed.append(["name": base, "error": err ?? "falhou"]) }
                self.notifyListeners("pickProgress", data: ["done": i + 1, "total": results.count])
            }
            call.resolve(["items": items, "failed": failed])
        }
    }

    /// A URL que a página consegue ler: capacitor://localhost/_capacitor_file_…
    /// (o Capacitor serve com CORS pra origem do server.url). Se a ponte não
    /// souber, o JS cai no readChunk.
    private func fileURL(for file: URL, origin: URL?) -> String? {
        bridge?.portablePath(fromLocalURL: file)?.absoluteString
    }

    private func pageOriginURL() -> URL? { bridge?.config.serverURL }

    static func hasGps(_ file: URL) -> Bool? {
        guard let src = CGImageSourceCreateWithURL(file as CFURL, nil),
              let props = CGImageSourceCopyPropertiesAtIndex(src, 0, nil) as? [CFString: Any] else { return nil }
        guard let gps = props[kCGImagePropertyGPSDictionary] as? [CFString: Any] else { return false }
        return gps[kCGImagePropertyGPSLatitude] != nil && gps[kCGImagePropertyGPSLongitude] != nil
    }

    // MARK: bytes JS ⇄ disco

    @objc func readChunk(_ call: CAPPluginCall) {
        guard let f = store.findPick(call.getString("pickId") ?? "") else { call.reject("pick desconhecido"); return }
        let offset = UInt64(max(0, call.getInt("offset") ?? 0))
        let length = min(call.getInt("length") ?? AmoraUploadPlugin.maxChunk, AmoraUploadPlugin.maxChunk)
        io.async {
            do {
                let h = try FileHandle(forReadingFrom: f)
                defer { try? h.close() }
                let size = h.seekToEndOfFile()
                h.seek(toFileOffset: min(offset, size))
                let data = h.readData(ofLength: max(0, length))
                call.resolve(["base64": data.base64EncodedString(), "size": size])
            } catch {
                call.reject("leitura: \(error.localizedDescription)")
            }
        }
    }

    @objc func putBlob(_ call: CAPPluginCall) {
        let id = call.getString("blobId") ?? UUID().uuidString.lowercased()
        guard let f = store.blobFile(id) else { call.reject("blobId inválido"); return }
        guard let data = Data(base64Encoded: call.getString("base64") ?? "") else { call.reject("base64 inválido"); return }
        io.async {
            do {
                if !FileManager.default.fileExists(atPath: f.path) { FileManager.default.createFile(atPath: f.path, contents: nil) }
                let h = try FileHandle(forWritingTo: f)
                defer { try? h.close() }
                h.seekToEndOfFile()
                h.write(data)
                let size = h.offsetInFile
                call.resolve(["blobId": id, "size": size])
            } catch {
                call.reject("gravação: \(error.localizedDescription)")
            }
        }
    }

    // MARK: fila

    @objc func enqueue(_ call: CAPPluginCall) {
        guard let spec = call.options as? [String: Any], let jobId = spec["jobId"] as? String, Store.validId(jobId) else {
            call.reject("jobId inválido (use [A-Za-z0-9-], até 64)")
            return
        }
        if let err = validate(spec) { call.reject(err); return }
        io.async {
            let job = self.store.createJob(spec)
            AmoraUploadQueue.shared.pump()
            call.resolve(job)
        }
    }

    /// Só sobe pro servidor da própria página, e só arquivos do armazenamento do plugin.
    private func validate(_ spec: [String: Any]) -> String? {
        guard let s = spec["url"] as? String, let target = URL(string: s), let host = target.host else { return "url inválida" }
        if target.scheme != "https" && host != "localhost" { return "url precisa ser https" }
        guard let page = pageOriginURL()?.host, page.caseInsensitiveCompare(host) == .orderedSame else {
            return "url fora do servidor do app: \(host)"
        }
        for f in spec["files"] as? [[String: Any]] ?? [] {
            guard let src = store.sourceFile(f["source"] as? [String: Any]), FileManager.default.fileExists(atPath: src.path) else {
                return "arquivo inexistente no envio: \(f["field"] ?? "?")"
            }
            if (f["field"] as? String ?? "").isEmpty || (f["filename"] as? String ?? "").isEmpty { return "field/filename obrigatórios" }
        }
        if let after = spec["after"] as? String, !after.isEmpty, !Store.validId(after) { return "after inválido" }
        return nil
    }

    @objc func listJobs(_ call: CAPPluginCall) {
        call.resolve(["jobs": store.listPublic()])
    }

    @objc func retry(_ call: CAPPluginCall) {
        let id = call.getString("jobId") ?? ""
        io.async {
            let ok = self.store.retry(id)
            if ok { AmoraUploadQueue.shared.pump() }
            call.resolve(["retried": ok])
        }
    }

    @objc func cancel(_ call: CAPPluginCall) {
        let id = call.getString("jobId") ?? ""
        let ok = store.cancel(id)
        if ok { AmoraUploadQueue.shared.cancel(id) }
        call.resolve(["cancelled": ok])
    }

    @objc func ack(_ call: CAPPluginCall) {
        let id = call.getString("jobId") ?? ""
        io.async {
            self.store.ack(id)
            call.resolve()
        }
    }

    @objc func release(_ call: CAPPluginCall) {
        let ids = (call.getArray("pickIds") as? [String]) ?? []
        io.async {
            self.store.release(ids)
            call.resolve()
        }
    }
}

@available(iOS 14, *)
extension AmoraUploadPlugin: PHPickerViewControllerDelegate {
    public func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
        picker.dismiss(animated: true)
        guard let call = pickCall else { return }
        pickCall = nil
        if results.isEmpty {
            call.resolve(["items": [Any](), "failed": [Any]()])
            return
        }
        copyPicked(results, call)
    }
}
