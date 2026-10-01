require 'json'

package = JSON.parse(File.read(File.join(__dir__, 'package.json')))

# Plugin LOCAL (dependência file: no capacitor/package.json) — o `cap sync ios`
# põe no Podfile. O módulo Swift se chama AmoraUpload: é o que o AppDelegate
# importa (ver o patch no run-ios.sh).
Pod::Spec.new do |s|
  s.name = 'AmoraUpload'
  s.version = package['version']
  s.summary = package['description']
  s.license = package['license']
  s.homepage = 'https://github.com/pedalhidro/amora'
  s.author = 'Pedal Hidrográfico'
  s.source = { :git => 'https://github.com/pedalhidro/amora.git', :tag => s.version.to_s }
  s.source_files = 'ios/Sources/**/*.swift'
  s.ios.deployment_target = '13.0'
  s.dependency 'Capacitor'
  s.swift_version = '5.9'
end
