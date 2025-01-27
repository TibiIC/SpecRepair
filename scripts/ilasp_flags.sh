ILASP files/update/based/minepump_aw_all.las -ml=100 --max-rule-length=10

python -m unittest tests.test_scripts.test_backtracking_repair_orchestrator.TestBacktrackingRepairOrchestrator.test_bfs_repair_spec_arbiter_non_unique