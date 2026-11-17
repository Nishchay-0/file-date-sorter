import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path/path.dart' as p;

import 'core/sorter_engine.dart';
import 'core/system_vault.dart';
import 'ui/theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const SmartFileOrganizerApp());
}

class SmartFileOrganizerApp extends StatefulWidget {
  const SmartFileOrganizerApp({super.key});

  @override
  State<SmartFileOrganizerApp> createState() => _SmartFileOrganizerAppState();
}

class _SmartFileOrganizerAppState extends State<SmartFileOrganizerApp> {
  ThemeMode _themeMode = ThemeMode.dark;

  void _toggleTheme() {
    setState(() {
      _themeMode = _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Smart File Organizer Suite Pro',
      debugShowCheckedModeBanner: false,
      themeMode: _themeMode,
      theme: ThemeData(
        brightness: Brightness.light,
        scaffoldBackgroundColor: GlassTheme.lightBg,
        fontFamily: 'Segoe UI',
        colorScheme: const ColorScheme.light(
          primary: GlassTheme.accentBlue,
          surface: GlassTheme.lightCard,
        ),
      ),
      darkTheme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: GlassTheme.darkBg,
        fontFamily: 'Segoe UI',
        colorScheme: const ColorScheme.dark(
          primary: GlassTheme.accentBlueDark,
          surface: GlassTheme.darkCard,
        ),
      ),
      home: HomeScreen(onToggleTheme: _toggleTheme),
    );
  }
}

class HomeScreen extends StatefulWidget {
  final VoidCallback onToggleTheme;
  const HomeScreen({super.key, required this.onToggleTheme});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String? _selectedDirectory;
  SortMode _sortMode = SortMode.date;
  bool _recursive = false;
  bool _isCollapsed = false;
  int _activeToolIndex = 0;

  bool _isProcessing = false;
  List<MoveOperation>? _plannedOperations;
  String? _statusMessage = 'Ready — pick a target folder to begin.';

  final List<Map<String, dynamic>> _tools = [
    {'icon': '📅', 'label': 'Organizer', 'mode': SortMode.date},
    {'icon': '🔍', 'label': 'Duplicates', 'mode': SortMode.category},
    {'icon': '👥', 'label': 'People', 'mode': SortMode.name},
    {'icon': '📦', 'label': 'Extractor', 'mode': SortMode.extension},
    {'icon': '🪄', 'label': 'Converter', 'mode': SortMode.category},
    {'icon': '🏷', 'label': 'Renamer', 'mode': SortMode.name},
    {'icon': '🧹', 'label': 'Cleaner', 'mode': SortMode.size},
    {'icon': '📊', 'label': 'Analytics', 'mode': SortMode.category},
    {'icon': '👁', 'label': 'Watcher', 'mode': SortMode.date},
    {'icon': '🚫', 'label': 'Exclusions', 'mode': SortMode.category},
  ];

  Future<void> _pickDirectory() async {
    final picked = await FilePicker.platform.getDirectoryPath();
    if (picked != null) {
      setState(() {
        _selectedDirectory = picked;
        _plannedOperations = null;
        _statusMessage = 'Folder loaded: $picked';
      });
      _runDryRunPreview();
    }
  }

  Future<void> _runDryRunPreview() async {
    if (_selectedDirectory == null) return;

    setState(() {
      _isProcessing = true;
      _statusMessage = 'Analyzing and simulating destination paths...';
    });

    try {
      final dir = Directory(_selectedDirectory!);
      final ops = await SorterEngine.planOrganization(
        directory: dir,
        sortMode: _sortMode,
        recursive: _recursive,
      );

      setState(() {
        _plannedOperations = ops;
        _statusMessage = 'Preview ready: ${ops.length} files scheduled to organize.';
      });
    } catch (e) {
      setState(() {
        _statusMessage = 'Error planning moves: $e';
      });
    } finally {
      setState(() => _isProcessing = false);
    }
  }

  Future<void> _executeMoves() async {
    if (_selectedDirectory == null || _plannedOperations == null) return;

    setState(() {
      _isProcessing = true;
      _statusMessage = 'Creating System Vault backup and organizing...';
    });

    try {
      final dir = Directory(_selectedDirectory!);
      final result = await SorterEngine.executeOrganization(
        directory: dir,
        operations: _plannedOperations!,
        dryRun: false,
      );

      setState(() {
        _plannedOperations = null;
        _statusMessage = '✓ Succeeded! Moved ${result.totalFiles} files. System Vault Armed.';
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('✓ Successfully organized ${result.totalFiles} files!'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      setState(() => _statusMessage = 'Error during execution: $e');
    } finally {
      setState(() => _isProcessing = false);
    }
  }

  Future<void> _undoLast() async {
    if (_selectedDirectory == null) return;
    try {
      final restored = await SystemVault.undoLastOperation(_selectedDirectory!);
      setState(() {
        _statusMessage = '✓ 1-Click Restore: Reverted $restored files to original paths.';
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Restored $restored files!'), backgroundColor: Colors.blue),
        );
      }
    } catch (e) {
      setState(() => _statusMessage = 'Undo error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final isMobile = MediaQuery.of(context).size.width < 700;

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // ── Top Navigation Bar ─────────────────────────────────────────
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: isDark ? GlassTheme.darkCard : GlassTheme.lightCard,
                border: Border(bottom: BorderSide(color: isDark ? GlassTheme.darkBorder : GlassTheme.lightBorder)),
              ),
              child: Row(
                children: [
                  const Text('⚡', style: TextStyle(fontSize: 22)),
                  const SizedBox(width: 8),
                  const Text(
                    'Smart File Organizer Pro',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  const Spacer(),
                  // Action buttons
                  IconButton(
                    icon: const Text('↩️', style: TextStyle(fontSize: 18)),
                    tooltip: '1-Click Undo',
                    onPressed: _selectedDirectory != null ? _undoLast : null,
                  ),
                  IconButton(
                    icon: const Text('🛡️', style: TextStyle(fontSize: 18)),
                    tooltip: 'System Vault',
                    onPressed: () {},
                  ),
                  IconButton(
                    icon: Text(isDark ? '☀️' : '🌙', style: const TextStyle(fontSize: 18)),
                    tooltip: 'Toggle Dark/Light Mode',
                    onPressed: widget.onToggleTheme,
                  ),
                ],
              ),
            ),

            // ── Main Body: Sidebar + Active Panel ──────────────────────────
            Expanded(
              child: Row(
                children: [
                  // Sidebar Toolbar
                  Container(
                    width: _isCollapsed ? 58 : 165,
                    padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 6),
                    decoration: BoxDecoration(
                      color: isDark ? GlassTheme.darkCard : GlassTheme.lightCard,
                      border: Border(right: BorderSide(color: isDark ? GlassTheme.darkBorder : GlassTheme.lightBorder)),
                    ),
                    child: Column(
                      children: [
                        // Collapse button
                        InkWell(
                          onTap: () => setState(() => _isCollapsed = !_isCollapsed),
                          borderRadius: BorderRadius.circular(8),
                          child: Container(
                            height: 32,
                            alignment: Alignment.center,
                            decoration: BoxDecoration(
                              color: isDark ? GlassTheme.darkCardAlt : GlassTheme.lightCardAlt,
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              _isCollapsed ? '☰' : '◂  Collapse',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11),
                            ),
                          ),
                        ),
                        const SizedBox(height: 8),
                        // 10 Tool buttons
                        Expanded(
                          child: ListView.builder(
                            itemCount: _tools.length,
                            itemBuilder: (context, idx) {
                              final item = _tools[idx];
                              final isSelected = _activeToolIndex == idx;
                              return Padding(
                                padding: const EdgeInsets.symmetric(vertical: 2),
                                child: InkWell(
                                  onTap: () {
                                    setState(() {
                                      _activeToolIndex = idx;
                                      _sortMode = item['mode'];
                                    });
                                    _runDryRunPreview();
                                  },
                                  borderRadius: BorderRadius.circular(10),
                                  child: Container(
                                    height: 36,
                                    padding: EdgeInsets.symmetric(horizontal: _isCollapsed ? 0 : 12),
                                    decoration: BoxDecoration(
                                      color: isSelected ? GlassTheme.accentBlue : Colors.transparent,
                                      borderRadius: BorderRadius.circular(10),
                                    ),
                                    alignment: _isCollapsed ? Alignment.center : Alignment.centerLeft,
                                    child: _isCollapsed
                                        ? Text(item['icon'], style: const TextStyle(fontSize: 18))
                                        : Row(
                                            children: [
                                              Text(item['icon'], style: const TextStyle(fontSize: 16)),
                                              const SizedBox(width: 10),
                                              Text(
                                                item['label'],
                                                style: TextStyle(
                                                  color: isSelected ? Colors.white : (isDark ? Colors.white70 : Colors.black87),
                                                  fontWeight: FontWeight.bold,
                                                  fontSize: 12,
                                                ),
                                              ),
                                            ],
                                          ),
                                  ),
                                ),
                              );
                            },
                          ),
                        ),
                      ],
                    ),
                  ),

                  // Active Content Panel
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          // Folder Picker Card
                          GlassTheme.glassCard(
                            context: context,
                            child: Row(
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const Text('Target Folder', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                      const SizedBox(height: 4),
                                      Text(
                                        _selectedDirectory ?? 'No directory selected yet.',
                                        style: TextStyle(
                                          color: isDark ? GlassTheme.darkTextSecondary : GlassTheme.lightTextSecondary,
                                          fontSize: 12,
                                        ),
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ],
                                  ),
                                ),
                                const SizedBox(width: 12),
                                ElevatedButton.icon(
                                  icon: const Icon(Icons.folder_open, size: 18),
                                  label: const Text('Pick Folder'),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: GlassTheme.accentBlue,
                                    foregroundColor: Colors.white,
                                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                  ),
                                  onPressed: _pickDirectory,
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: 12),

                          // Strategy & Options Row
                          Row(
                            children: [
                              // Sort Strategy Dropdown
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 12),
                                decoration: BoxDecoration(
                                  color: isDark ? GlassTheme.darkCardAlt : GlassTheme.lightCardAlt,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: DropdownButton<SortMode>(
                                  value: _sortMode,
                                  underline: const SizedBox(),
                                  dropdownColor: isDark ? const Color(0xFF2C2C2E) : Colors.white,
                                  items: const [
                                    DropdownMenuItem(value: SortMode.date, child: Text('Sort by Date (YYYY/MM)')),
                                    DropdownMenuItem(value: SortMode.category, child: Text('Sort by Category')),
                                    DropdownMenuItem(value: SortMode.name, child: Text('Smart Name Grouping')),
                                    DropdownMenuItem(value: SortMode.extension, child: Text('Sort by Extension')),
                                    DropdownMenuItem(value: SortMode.size, child: Text('Sort by File Size')),
                                  ],
                                  onChanged: (val) {
                                    if (val != null) {
                                      setState(() => _sortMode = val);
                                      _runDryRunPreview();
                                    }
                                  },
                                ),
                              ),
                              const SizedBox(width: 12),
                              // Recursive switch
                              Row(
                                children: [
                                  Checkbox(
                                    value: _recursive,
                                    activeColor: GlassTheme.accentBlue,
                                    onChanged: (v) {
                                      setState(() => _recursive = v ?? false);
                                      _runDryRunPreview();
                                    },
                                  ),
                                  const Text('Include Subfolders', style: TextStyle(fontSize: 12)),
                                ],
                              ),
                              const Spacer(),
                              // Execute Action Button
                              ElevatedButton(
                                onPressed: (_plannedOperations != null && _plannedOperations!.isNotEmpty && !_isProcessing)
                                    ? _executeMoves
                                    : null,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.green,
                                  foregroundColor: Colors.white,
                                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                ),
                                child: Text('Execute (${_plannedOperations?.length ?? 0} moves)'),
                              ),
                            ],
                          ),

                          const SizedBox(height: 12),

                          // Preview Table / Empty State
                          Expanded(
                            child: GlassTheme.glassCard(
                              context: context,
                              padding: const EdgeInsets.all(8),
                              child: _plannedOperations == null
                                  ? Center(
                                      child: Text(
                                        _statusMessage ?? 'Pick a folder to see live preview.',
                                        style: TextStyle(color: isDark ? Colors.white60 : Colors.black54),
                                      ),
                                    )
                                  : ListView.separated(
                                      itemCount: _plannedOperations!.length,
                                      separatorBuilder: (_, __) => Divider(
                                        height: 1,
                                        color: isDark ? Colors.white12 : Colors.black12,
                                      ),
                                      itemBuilder: (context, idx) {
                                        final op = _plannedOperations![idx];
                                        return Padding(
                                          padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 8),
                                          child: Row(
                                            children: [
                                              Text(op.category, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
                                              const SizedBox(width: 12),
                                              Expanded(
                                                flex: 2,
                                                child: Text(
                                                  p.basename(op.sourcePath),
                                                  style: const TextStyle(fontSize: 12),
                                                  overflow: TextOverflow.ellipsis,
                                                ),
                                              ),
                                              const Icon(Icons.arrow_forward, size: 14, color: Colors.blue),
                                              const SizedBox(width: 8),
                                              Expanded(
                                                flex: 3,
                                                child: Text(
                                                  p.relative(op.destinationPath, from: _selectedDirectory!),
                                                  style: const TextStyle(color: Colors.green, fontSize: 12),
                                                  overflow: TextOverflow.ellipsis,
                                                ),
                                              ),
                                            ],
                                          ),
                                        );
                                      },
                                    ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // ── Bottom Status Bar ──────────────────────────────────────────
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              color: isDark ? const Color(0xFF141416) : const Color(0xFFE5E5EA),
              child: Row(
                children: [
                  Text(_statusMessage ?? 'Ready', style: const TextStyle(fontSize: 11)),
                  const Spacer(),
                  const Text('🛡️ System Vault: Armed', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
