import Foundation

/// Alarmın kaydedilmesini engelleyen sorunlar.
///
/// Yalnızca **tamamlanamaz** duruma yol açan şeyler buraya girer. Boş başlık
/// veya tekrar günü seçilmemiş olması sorun değildir; ilki yerine varsayılan
/// gösterilir, ikincisi tek seferlik alarm demektir.
public enum AlarmValidationIssue: Equatable, Sendable, Identifiable {
    /// Fotoğraf görevine ne çekileceği yazılmamış — kullanıcı alarm çaldığında
    /// ne yapması gerektiğini bilemez ve görevi tamamlayamaz.
    case photoTaskMissingPrompt(taskID: UUID)

    public var id: String {
        switch self {
        case .photoTaskMissingPrompt(let taskID): "photoPrompt-\(taskID)"
        }
    }
}

public extension Alarm {

    var validationIssues: [AlarmValidationIssue] {
        tasks.compactMap { task in
            if case .photo(let prompt) = task.configuration, prompt.trimmed().isEmpty {
                return .photoTaskMissingPrompt(taskID: task.id)
            }
            return nil
        }
    }

    var canBeSaved: Bool {
        validationIssues.isEmpty
    }
}
