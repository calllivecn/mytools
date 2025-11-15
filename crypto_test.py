import io
import os
import sys
import unittest
import tempfile

from pathlib import Path

import crypto

def run_main(argv):
    """在受控环境下运行 crypto.main，捕获 stdout/stderr，并返回 (exit_code, stdout, stderr)."""
    saved_argv = sys.argv
    saved_stdout = sys.stdout
    saved_stderr = sys.stderr
    out = io.StringIO()
    err = io.StringIO()
    try:
        sys.argv = ['crypto.py'] + argv
        sys.stdout = out
        sys.stderr = err
        try:
            crypto.main()
            return 0, out.getvalue(), err.getvalue()
        except SystemExit as e:
            return (e.code, out.getvalue(), err.getvalue())
    finally:
        sys.argv = saved_argv
        sys.stdout = saved_stdout
        sys.stderr = saved_stderr


class IntegrationTests(unittest.TestCase):
    def test_parse_flag(self):
        code, out, err = run_main(['--parse'])
        self.assertIn('parse=True', out)
        self.assertEqual(code, 0)

    def test_fileinfo_shows_metadata(self):
        # 准备一个带 header 的文件
        tmpdir = tempfile.TemporaryDirectory()
        p = Path(tmpdir.name) / "hdr.bin"
        header = crypto.FileFormat()
        header.set_prompt("unit-prompt")
        with open(p, "wb") as f:
            f.write(header.encode())  # 不写 payload
        code, out, err = run_main(['-I', str(p)])
        self.assertEqual(code, 0)
        self.assertIn('File Version:', out)
        self.assertIn('IV:', out)
        self.assertIn('Salt:', out)
        self.assertIn('Password Prompt:', out)
        tmpdir.cleanup()

    def test_encrypt_decrypt_with_password_files(self):
        tmpdir = tempfile.TemporaryDirectory()
        in_file = Path(tmpdir.name) / "plain.bin"
        enc_file = Path(tmpdir.name) / "enc.bin"
        dec_file = Path(tmpdir.name) / "dec.bin"
        data = (b"Hello Integration Test!\n" * 50)
        with open(in_file, "wb") as f:
            f.write(data)

        # 加密（使用 -k 和 -p）
        code, out, err = run_main(['-k', 's3cr3t', '-p', 'myprompt', '-i', str(in_file), '-o', str(enc_file)])
        self.assertEqual(code, 0)
        self.assertTrue(enc_file.exists() and enc_file.stat().st_size > 0)

        # 解密（使用 -d 和 -k）
        code, out, err = run_main(['-d', '-k', 's3cr3t', '-i', str(enc_file), '-o', str(dec_file)])
        self.assertEqual(code, 0)
        with open(dec_file, "rb") as f:
            got = f.read()
        self.assertEqual(got, data)
        tmpdir.cleanup()

    def test_encrypt_decrypt_with_keyfile(self):
        tmpdir = tempfile.TemporaryDirectory()
        in_file = Path(tmpdir.name) / "plain2.bin"
        enc_file = Path(tmpdir.name) / "enc2.bin"
        dec_file = Path(tmpdir.name) / "dec2.bin"

        data = b"Keyfile mode plaintext\n" * 30
        with open(in_file, "wb") as f:
            f.write(data)

        # 生成两个小的 keyfile（确保大小 >= offset + keysize）
        kf1 = Path(tmpdir.name) / "kf1.bin"
        kf2 = Path(tmpdir.name) / "kf2.bin"
        with open(kf1, "wb") as f:
            f.write(os.urandom(64))
        with open(kf2, "wb") as f:
            f.write(os.urandom(64))

        # 使用较小的 --keysize 以加快测试
        keysize = "16"
        offsets = ["0", "0"]
        # 加密（使用 --keyfile/--offset/--keysize）
        args_enc = ['--keyfile', str(kf1), str(kf2), '--offset'] + offsets + ['--keysize', keysize, '-i', str(in_file), '-o', str(enc_file)]
        code, out, err = run_main(args_enc)
        self.assertEqual(code, 0)
        self.assertTrue(enc_file.exists() and enc_file.stat().st_size > 0)

        # 解密（相同的 keyfile 参数，加上 -d）
        args_dec = ['-d', '--keyfile', str(kf1), str(kf2), '--offset'] + offsets + ['--keysize', keysize, '-i', str(enc_file), '-o', str(dec_file)]
        code, out, err = run_main(args_dec)
        self.assertEqual(code, 0)
        with open(dec_file, "rb") as f:
            got = f.read()
        self.assertEqual(got, data)
        tmpdir.cleanup()

    def test_verbose_and_keycount_parsing(self):
        tmpdir = tempfile.TemporaryDirectory()
        in_file = Path(tmpdir.name) / "plain3.bin"
        out_file = Path(tmpdir.name) / "out3.bin"
        with open(in_file, "wb") as f:
            f.write(b"x" * 128)

        # 只测试解析及运行，不断言日志内容（logger 在模块中被全局设置）
        code, out, err = run_main(['-k', 'pw', '-v', '-v', '--key-count', '-i', str(in_file), '-o', str(out_file)])
        self.assertEqual(code, 0)
        # 输出文件应创建
        self.assertTrue(out_file.exists())
        tmpdir.cleanup()


if __name__ == "__main__":
    unittest.main()
