import 'package:flutter/material.dart';

import '../../core/models/alarm.dart';
import '../../core/models/alarm_task.dart';
import '../../design/theme.dart';
import '../../localization/strings.dart';

/// Ana sayfadaki tek alarm kartı.
///
/// Yedi gün rozeti yerine tek satır özet ("Hafta içi") kullanılıyor: liste
/// ekranında okunan şey saat ve başlık, günlerin tek tek hangileri olduğu
/// değil.
class AlarmCard extends StatelessWidget {
  const AlarmCard({super.key, required this.alarm, required this.onToggle, this.onTap});

  final Alarm alarm;
  final ValueChanged<bool> onToggle;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: alarm.isEnabled ? 1 : 0.34,
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(AppTheme.spaceMd + 4),
          decoration: AppTheme.card(),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Text(alarm.time.displayText, style: AppTheme.cardTime),
                  const Spacer(),
                  Switch(
                    value: alarm.isEnabled,
                    onChanged: onToggle,
                    activeThumbColor: Colors.white,
                    activeTrackColor: AppTheme.accent,
                  ),
                ],
              ),
              const SizedBox(height: AppTheme.spaceSm + 2),
              Row(
                children: [
                  Flexible(
                    child: Text(
                      alarm.displayTitle,
                      style: AppTheme.callout,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: AppTheme.spaceSm + 2),
                  Container(
                    width: 3,
                    height: 3,
                    decoration: BoxDecoration(
                      color: AppTheme.textQuaternary,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: AppTheme.spaceSm + 2),
                  Text(
                    alarm.repeatSummary,
                    style: AppTheme.footnote.copyWith(
                      fontSize: 15,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ],
              ),
              if (alarm.requiresTasks) ...[
                const SizedBox(height: AppTheme.spaceSm + 6),
                Row(
                  children: [
                    for (final task in alarm.tasks) ...[
                      _TaskIcon(kind: task.kind),
                      const SizedBox(width: 7),
                    ],
                    const SizedBox(width: 2),
                    Text(
                      Strings.taskCount(alarm.tasks.length),
                      style: AppTheme.footnote.copyWith(color: AppTheme.textTertiary),
                    ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _TaskIcon extends StatelessWidget {
  const _TaskIcon({required this.kind});

  final TaskKind kind;

  static const _icons = {
    TaskKind.shake: Icons.vibration_rounded,
    TaskKind.math: Icons.calculate_outlined,
    TaskKind.photo: Icons.photo_camera_rounded,
  };

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 30,
      height: 30,
      decoration: BoxDecoration(
        color: AppTheme.fill,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Icon(_icons[kind], size: 16, color: AppTheme.accentBright),
    );
  }
}
