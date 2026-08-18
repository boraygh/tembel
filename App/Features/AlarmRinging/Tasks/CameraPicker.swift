import SwiftUI
import UIKit

/// Kamerayı açan basit sarmalayıcı.
///
/// `UIImagePickerController` seçildi çünkü tek bir fotoğraf çekmek için
/// AVFoundation ile özel bir kamera arayüzü kurmaktan çok daha az yüzey
/// alanına sahip ve iznin reddi gibi durumları sistem kendi ele alıyor.
/// İleride nesne tanıma eklenirse burası AVFoundation'a geçirilebilir —
/// çağıran taraf yalnızca `onCapture` görüyor.
struct CameraPicker: UIViewControllerRepresentable {

    let onCapture: (UIImage) -> Void
    let onCancel: () -> Void

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let controller = UIImagePickerController()
        controller.delegate = context.coordinator
        controller.allowsEditing = false

        if UIImagePickerController.isSourceTypeAvailable(.camera) {
            controller.sourceType = .camera
        } else {
            // Simulator'da kamera yoktur. Gerçek cihazda bu dala düşülmez;
            // düşülürse de görev tamamlanabilsin diye kütüphaneye geçilir.
            controller.sourceType = .photoLibrary
        }

        return controller
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}

    func makeCoordinator() -> Coordinator {
        Coordinator(onCapture: onCapture, onCancel: onCancel)
    }

    final class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {

        private let onCapture: (UIImage) -> Void
        private let onCancel: () -> Void

        init(onCapture: @escaping (UIImage) -> Void, onCancel: @escaping () -> Void) {
            self.onCapture = onCapture
            self.onCancel = onCancel
        }

        func imagePickerController(
            _ picker: UIImagePickerController,
            didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey: Any]
        ) {
            if let image = info[.originalImage] as? UIImage {
                onCapture(image)
            } else {
                onCancel()
            }
        }

        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            onCancel()
        }
    }
}
