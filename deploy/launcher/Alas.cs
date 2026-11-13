using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

internal static class Launcher
{
    [STAThread]
    private static int Main()
    {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        string log = Path.Combine(root, "log", "launcher.log");
        try
        {
            if (!File.Exists(Path.Combine(root, "gui.py")))
                throw new InvalidOperationException("Extract the desktop package into the Alas source folder first.");

            string desktop = Path.Combine(root, "webapp", "dist", "win-unpacked", "alas.exe");
            if (!File.Exists(desktop))
                throw new FileNotFoundException("Desktop files are missing. Rebuild with npm run package:win in webapp.", desktop);

            Directory.CreateDirectory(Path.GetDirectoryName(log));
            if (!File.Exists(Path.Combine(root, ".venv", "Scripts", "python.exe")) &&
                !File.Exists(Path.Combine(root, "toolkit", "python.exe")))
            {
                var sync = new ProcessStartInfo("uv", "sync --locked --no-dev --inexact");
                sync.WorkingDirectory = root;
                sync.UseShellExecute = false;
                sync.CreateNoWindow = true;
                sync.RedirectStandardOutput = true;
                sync.RedirectStandardError = true;
                using (var writer = new StreamWriter(log, true))
                using (var process = new Process())
                {
                    process.StartInfo = sync;
                    process.OutputDataReceived += delegate(object sender, DataReceivedEventArgs entry)
                    {
                        if (entry.Data != null) lock (writer) writer.WriteLine(entry.Data);
                    };
                    process.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs entry)
                    {
                        if (entry.Data != null) lock (writer) writer.WriteLine(entry.Data);
                    };
                    process.Start();
                    process.BeginOutputReadLine();
                    process.BeginErrorReadLine();
                    process.WaitForExit();
                    if (process.ExitCode != 0)
                        throw new InvalidOperationException("Dependency installation failed. See log/launcher.log.");
                }
            }

            var start = new ProcessStartInfo(desktop);
            start.WorkingDirectory = root;
            start.UseShellExecute = false;
            start.EnvironmentVariables["ALAS_ROOT"] = root;
            start.EnvironmentVariables.Remove("ELECTRON_RUN_AS_NODE");
            Process.Start(start);
            return 0;
        }
        catch (Exception error)
        {
            MessageBox.Show(error.Message, "Alas startup failed", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
