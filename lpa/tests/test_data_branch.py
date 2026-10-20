# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify persistence in an isolated local remote, without modifying GitHub."""
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'data-branch.sh'


class DataBranch(unittest.TestCase):
    def test_bootstrap_and_restore_keep_application_history_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            remote, repo, state = temp/'remote.git', temp/'repo', temp/'state'
            def run(*args, cwd=None):
                return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout
            run('git','init','--bare',str(remote))
            run('git','init','-b','lpa',str(repo))
            (repo/'application.py').write_text('# application\n')
            run('git','add','application.py',cwd=repo)
            run('git','-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','application',cwd=repo)
            run('git','remote','add','origin',str(remote),cwd=repo)
            original=run('git','rev-parse','HEAD',cwd=repo).strip()
            run(str(SCRIPT),'prepare',str(state),cwd=repo)
            self.assertFalse((state/'application.py').exists())
            (state/'summary.json').write_text('{"observations": 1}\n')
            run(str(SCRIPT),'save',str(state),cwd=repo)
            self.assertEqual(run('git','rev-parse','HEAD',cwd=repo).strip(),original)
            run('git','worktree','remove',str(state),cwd=repo)
            run(str(SCRIPT),'prepare',str(state),cwd=repo)
            self.assertTrue((state/'summary.json').exists())
            self.assertFalse((state/'application.py').exists())
            self.assertEqual(run('git','status','--porcelain',cwd=repo),'')
            # A repeated save must create neither another commit nor a force push.
            old=run('git','rev-parse','HEAD',cwd=state)
            run(str(SCRIPT),'save',str(state),cwd=repo)
            self.assertEqual(run('git','rev-parse','HEAD',cwd=state),old)
