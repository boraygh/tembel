import 'package:flutter/material.dart';

import 'core/models/alarm.dart';
import 'core/models/alarm_task.dart';
import 'core/models/clock_time.dart';
import 'core/models/weekday.dart';
import 'design/theme.dart';
import 'features/home/home_screen.dart';
import 'localization/strings.dart';

void main() => runApp(const TembelApp());

class TembelApp extends StatelessWidget {
  const TembelApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: Strings.appName,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.data,
      home: HomeScreen(alarms: sampleAlarms),
    );
  }
}

/// Geliştirme sırasında ekranın dolu görünmesi için örnek veri.
///
/// Kalıcı kayıt bağlandığında kaldırılacak.
final List<Alarm> sampleAlarms = [
  Alarm(
    id: 'sample-1',
    title: 'İşe Kalk',
    time: ClockTime(7, 30),
    repeatDays: Weekday.weekdays,
    tasks: const [
      AlarmTask(id: 's1t1', configuration: ShakeConfiguration(count: 10)),
      AlarmTask(
        id: 's1t2',
        configuration:
            MathConfiguration(difficulty: MathDifficulty.medium, questionCount: 2),
      ),
      AlarmTask(id: 's1t3', configuration: PhotoConfiguration(prompt: 'Kahve makinesi')),
    ],
  ),
  Alarm(
    id: 'sample-2',
    title: 'Spor',
    time: ClockTime(8, 45),
    repeatDays: const {Weekday.tuesday, Weekday.thursday},
    tasks: const [
      AlarmTask(id: 's2t1', configuration: ShakeConfiguration(count: 25)),
      AlarmTask(
        id: 's2t2',
        configuration:
            MathConfiguration(difficulty: MathDifficulty.hard, questionCount: 3),
      ),
    ],
  ),
  Alarm(
    id: 'sample-3',
    title: 'Erken Kalk',
    time: ClockTime(6, 15),
    repeatDays: Weekday.weekend,
    isEnabled: false,
    tasks: const [
      AlarmTask(
        id: 's3t1',
        configuration:
            MathConfiguration(difficulty: MathDifficulty.easy, questionCount: 1),
      ),
    ],
  ),
];
