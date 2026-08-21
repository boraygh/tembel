import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/models/alarm.dart';
import '../../core/scheduling/alarm_scheduler.dart';
import '../../design/theme.dart';
import '../../localization/strings.dart';
import 'alarm_card.dart';

/// Ana sayfa — kurulu alarmların listesi.
///
/// Şu an bellekte örnek veriyle çalışıyor; kalıcı kayıt ve alarm düzenleyici
/// sonraki adımda bağlanacak.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.alarms});

  final List<Alarm> alarms;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late List<Alarm> _alarms = widget.alarms.sortedForDisplay();
  Timer? _ticker;
  DateTime _now = DateTime.now();

  @override
  void initState() {
    super.initState();
    // Geri sayım ekranda donup kalmasın diye dakikada bir yenilenir.
    _ticker = Timer.periodic(const Duration(minutes: 1), (_) {
      if (mounted) setState(() => _now = DateTime.now());
    });
  }

  @override
  void dispose() {
    _ticker?.cancel();
    super.dispose();
  }

  void _setEnabled(Alarm alarm, bool isEnabled) {
    setState(() {
      _alarms = [
        for (final a in _alarms) a.id == alarm.id ? a.copyWith(isEnabled: isEnabled) : a,
      ].sortedForDisplay();
    });
  }

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(gradient: AppTheme.pageGradient),
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _header(),
            _nextAlarmSummary(),
            Expanded(child: _alarms.isEmpty ? _emptyState() : _list()),
          ],
        ),
      ),
    );
  }

  Widget _header() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(
          AppTheme.spaceLg, AppTheme.spaceSm, AppTheme.spaceLg, AppTheme.spaceSm),
      child: Row(
        children: [
          const Text(Strings.alarmsTab, style: AppTheme.largeTitle),
          const Spacer(),
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(color: AppTheme.fill, shape: BoxShape.circle),
            child: const Icon(Icons.add_rounded, color: AppTheme.accentBright, size: 24),
          ),
        ],
      ),
    );
  }

  Widget _nextAlarmSummary() {
    final next = AlarmScheduler.nextAlarm(_alarms, _now);
    final remaining =
        next == null ? null : Strings.timeRemaining(next.date, _now);

    return Padding(
      padding: const EdgeInsets.fromLTRB(
          AppTheme.spaceLg, 0, AppTheme.spaceLg, AppTheme.spaceLg),
      child: Row(
        children: [
          Container(
            width: 7,
            height: 7,
            decoration: BoxDecoration(
              color: remaining == null ? AppTheme.textQuaternary : AppTheme.accent,
              shape: BoxShape.circle,
              boxShadow: remaining == null
                  ? null
                  : [BoxShadow(color: AppTheme.accent, blurRadius: 10)],
            ),
          ),
          const SizedBox(width: 9),
          if (remaining == null)
            Text(
              Strings.noEnabledAlarm,
              style: AppTheme.footnote.copyWith(
                  fontSize: 14, color: AppTheme.textSecondary),
            )
          else
            Text.rich(
              TextSpan(
                text: Strings.nextAlarmPrefix,
                style: AppTheme.footnote
                    .copyWith(fontSize: 14, color: AppTheme.textSecondary),
                children: [
                  TextSpan(
                    text: remaining,
                    style: AppTheme.footnote.copyWith(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: Colors.white.withValues(alpha: 0.92),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _list() {
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(
          AppTheme.spaceLg, 0, AppTheme.spaceLg, AppTheme.spaceXl),
      itemCount: _alarms.length,
      separatorBuilder: (_, _) => const SizedBox(height: 13),
      itemBuilder: (context, index) {
        final alarm = _alarms[index];
        return AlarmCard(
          alarm: alarm,
          onToggle: (value) => _setEnabled(alarm, value),
        );
      },
    );
  }

  Widget _emptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 44),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.alarm_rounded, size: 72, color: AppTheme.accent),
            const SizedBox(height: AppTheme.spaceLg),
            const Text(Strings.emptyTitle, style: AppTheme.title),
            const SizedBox(height: 10),
            Text(
              Strings.emptyMessage,
              textAlign: TextAlign.center,
              style: AppTheme.footnote
                  .copyWith(fontSize: 15, color: AppTheme.textSecondary, height: 1.5),
            ),
            const SizedBox(height: AppTheme.spaceLg),
            Container(
              height: 54,
              padding: const EdgeInsets.symmetric(horizontal: 28),
              decoration: BoxDecoration(
                gradient: AppTheme.emberGradient,
                borderRadius: BorderRadius.circular(17),
                boxShadow: AppTheme.emberShadow,
              ),
              alignment: Alignment.center,
              child: const Text(
                Strings.emptyAction,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.background,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
