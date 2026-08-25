import sys, traceback
mods = ['cli','gui','sorter_core','settings_manager','hashing','watcher_service','version','build_exe','face_sort'] + \
       [f'gui_modules.{m}' for m in ['app','components','context_menu',
                                    'views.tab_analytics','views.tab_cleaner','views.tab_converter',
                                    'views.tab_duplicates','views.tab_exclusions','views.tab_extractor',
                                    'views.tab_people','views.tab_renamer','views.tab_sorter','views.tab_watcher']]
failed = []
for m in mods:
    try:
        __import__(m)
    except Exception as e:
        failed.append((m, e))
        print(f'Failed: {m} -> {e}')
if failed:
    sys.exit(1)
else:
    print('All imports succeeded')