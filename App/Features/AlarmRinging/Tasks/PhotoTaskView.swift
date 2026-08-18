import AVFoundation
import SwiftUI
import UIKit

/// Fotoğraf görevi.
///
/// MVP'de nesne tanıma yok: kullanıcı fotoğrafı çeker ve doğru şeyi çektiğini
/// kendisi onaylar. Amaç kullanıcıyı yataktan kaldırmak, onu denetlemek değil —
/// kendini kandırmak isteyen zaten alarmı kurmaz.
///
/// Tanıma eklendiğinde değişecek tek yer `confirmationArea`: onay butonunun
/// yerine `Vision`/`Core ML` sonucu geçer. Çekim ve izin akışı aynı kalır.
struct PhotoTaskView: View {

    let prompt: String
    let onComplete: () -> Void

    @State private var capturedImage: UIImage?
    @State private var isPresentingCamera = false
    @State private var isPermissionDenied = false

    var body: some View {
        VStack(spacing: Theme.Spacing.lg) {
            Spacer(minLength: 0)

            promptArea

            if let capturedImage {
                preview(capturedImage)
            } else if isPermissionDenied {
                permissionDeniedArea
            } else {
                captureButton
            }

            Spacer(minLength: 0)

            Text(AppStrings.PhotoTask.privacyNote)
                .font(Theme.Typography.caption)
                .foregroundStyle(Theme.Palette.textTertiary)
                .multilineTextAlignment(.center)
                .padding(.bottom, Theme.Spacing.md)
        }
        .padding(.horizontal, Theme.Spacing.lg)
        .fullScreenCover(isPresented: $isPresentingCamera) {
            CameraPicker(
                onCapture: { image in
                    capturedImage = image
                    isPresentingCamera = false
                },
                onCancel: { isPresentingCamera = false }
            )
            .ignoresSafeArea()
        }
    }

    private var promptArea: some View {
        VStack(spacing: Theme.Spacing.sm) {
            Image(systemName: "camera.viewfinder")
                .font(.system(size: 36, weight: .light))
                .foregroundStyle(Theme.Palette.accent)
            Text(prompt)
                .font(Theme.Typography.title)
                .tracking(Theme.Tracking.title)
                .foregroundStyle(Theme.Palette.textPrimary)
                .multilineTextAlignment(.center)
        }
    }

    private var captureButton: some View {
        PrimaryButton(
            title: AppStrings.PhotoTask.openCamera,
            systemImage: "camera.fill"
        ) {
            requestAccessAndPresent()
        }
    }

    private func preview(_ image: UIImage) -> some View {
        VStack(spacing: Theme.Spacing.md) {
            Image(uiImage: image)
                .resizable()
                .scaledToFill()
                .frame(height: 240)
                .clipShape(RoundedRectangle(cornerRadius: Theme.Radius.card, style: .continuous))

            PrimaryButton(
                title: AppStrings.PhotoTask.confirm,
                systemImage: "checkmark"
            ) {
                // Fotoğraf yalnızca bellekte tutuldu; hiçbir yere yazılmadı.
                capturedImage = nil
                onComplete()
            }

            Button(AppStrings.PhotoTask.retake) {
                capturedImage = nil
                requestAccessAndPresent()
            }
            .font(Theme.Typography.callout)
            .foregroundStyle(Theme.Palette.textSecondary)
        }
    }

    private var permissionDeniedArea: some View {
        VStack(spacing: Theme.Spacing.sm) {
            Text(AppStrings.PhotoTask.permissionDenied)
                .font(Theme.Typography.headline)
                .foregroundStyle(Theme.Palette.textPrimary)
            Text(AppStrings.PhotoTask.permissionHelp)
                .font(Theme.Typography.footnote)
                .foregroundStyle(Theme.Palette.textSecondary)
                .multilineTextAlignment(.center)
        }
    }

    /// Kamera iznini ister ve sonucuna göre kamerayı açar.
    ///
    /// İzin reddedilmişse görev tamamlanamaz — bu bilinçli bir çıkmaz değil,
    /// kullanıcıya durumu açıkça söyleyip Ayarlar'a yönlendiriyoruz. Alarm
    /// zinciri gelmeye devam ettiği için kullanıcı izni açıp devam edebilir.
    private func requestAccessAndPresent() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            isPresentingCamera = true

        case .notDetermined:
            // Completion handler yerine async biçim: geri çağrım @Sendable
            // olduğu için görünümün durumuna oradan dokunmak Swift 6
            // eşzamanlılık kurallarıyla çakışır.
            Task {
                let granted = await AVCaptureDevice.requestAccess(for: .video)
                if granted {
                    isPresentingCamera = true
                } else {
                    isPermissionDenied = true
                }
            }

        case .denied, .restricted:
            isPermissionDenied = true

        @unknown default:
            isPermissionDenied = true
        }
    }
}

#Preview {
    ZStack {
        Theme.Gradients.page.ignoresSafeArea()
        PhotoTaskView(prompt: "Mutfaktaki kahve makinesi") {}
    }
    .preferredColorScheme(.dark)
}
