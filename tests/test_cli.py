import subprocess, sys, shutil
from pathlib import Path

def run_cmd(args, cwd):
    proc = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode, proc.stdout, proc.stderr

def test_single_file(tmp_path: Path):
    proj = Path(__file__).resolve().parents[1]
    input_csv = proj / "examples" / "operations.sample.csv"
    out_dir = tmp_path / "out1"
    code, out, err = run_cmd([sys.executable, "-m", "tbank2qif", "-i", str(input_csv), "--out-dir", str(out_dir)], cwd=proj)
    assert code == 0, err
    assert (out_dir / "import.qif").exists()
    assert (out_dir / "quicken.csv").exists()

def test_batch_with_combined(tmp_path: Path):
    proj = Path(__file__).resolve().parents[1]
    inp_dir = tmp_path / "inp"
    out_dir = tmp_path / "out2"
    inp_dir.mkdir(parents=True, exist_ok=True)
    # copy example twice under different names
    src = proj / "examples" / "operations.sample.csv"
    shutil.copy(src, inp_dir / "a.csv")
    shutil.copy(src, inp_dir / "b.csv")

    code, out, err = run_cmd([sys.executable, "-m", "tbank2qif", "--input-dir", str(inp_dir), "--output-dir", str(out_dir), "--combined"], cwd=proj)
    assert code == 0, err
    # per-file dirs
    assert (out_dir / "a" / "import.qif").exists()
    assert (out_dir / "b" / "import.qif").exists()
    # combined
    assert (out_dir / "combined.qif").exists()

def test_encoding_option(tmp_path: Path):
    proj = Path(__file__).resolve().parents[1]
    # reuse example; just ensure flag is accepted
    input_csv = proj / "examples" / "operations.sample.csv"
    out_dir = tmp_path / "out3"
    code, out, err = run_cmd([sys.executable, "-m", "tbank2qif", "-i", str(input_csv), "--out-dir", str(out_dir), "--encoding", "utf-8"], cwd=proj)
    assert code == 0, err
    assert (out_dir / "import.qif").exists()
