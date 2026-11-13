const {strict: assert} = require('assert');
const {spawn, execFileSync} = require('child_process');
const fs = require('fs');
const http = require('http');
const net = require('net');
const os = require('os');
const path = require('path');
const yaml = require('yaml');
const { _electron: electron } = require('playwright');

const sourceRoot = path.resolve(__dirname, '../..');
const testRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'alas desktop smoke '));
const artifacts = path.join(sourceRoot, 'webapp/dist/output/playwright');
const runtime = path.join(testRoot, 'webapp/dist/win-unpacked');
const environment = {...process.env};
delete environment.ELECTRON_RUN_AS_NODE;
delete environment.ALAS_ROOT;

async function unusedPort() {
  const server = net.createServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const port = server.address().port;
  await new Promise(resolve => server.close(resolve));
  return port;
}

async function waitUntil(check, message) {
  const deadline = Date.now() + 60000;
  while (Date.now() < deadline) {
    try {
      if (await check()) return;
    } catch (error) {
      if (!error.message.includes('Execution context was destroyed')) throw error;
    }
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error(message);
}

function responds(port) {
  return new Promise(resolve => {
    const request = http.get(`http://127.0.0.1:${port}/`, response => {
      response.resume();
      resolve(response.statusCode === 200);
    });
    request.on('error', () => resolve(false));
    request.setTimeout(1000, () => request.destroy());
  });
}

function killTree(processId) {
  try {
    execFileSync('taskkill', ['/PID', String(processId), '/T', '/F'], {stdio: 'ignore'});
  } catch (error) {
    if (!error.status) throw error;
  }
}

(async () => {
  let app;
  let appProcessId;
  let nativeProcessId;
  try {
    for (const directory of ['module', 'assets', 'bin', 'campaign', 'deploy', 'submodule', '.venv']) {
      fs.symlinkSync(path.join(sourceRoot, directory), path.join(testRoot, directory), 'junction');
    }
    fs.mkdirSync(path.dirname(runtime), {recursive: true});
    fs.symlinkSync(path.join(sourceRoot, 'webapp/dist/win-unpacked'), runtime, 'junction');
    for (const file of ['gui.py', 'alas.py', 'pyproject.toml', 'uv.lock', '.python-version', 'Alas.exe']) {
      fs.copyFileSync(path.join(sourceRoot, file), path.join(testRoot, file));
    }
    fs.mkdirSync(path.join(testRoot, 'config'));
    for (const file of fs.readdirSync(path.join(sourceRoot, 'config'))) {
      if (/^(deploy\.template|template)/.test(file)) {
        fs.copyFileSync(path.join(sourceRoot, 'config', file), path.join(testRoot, 'config', file));
      }
    }
    const settings = yaml.parse(fs.readFileSync(path.join(testRoot, 'config/deploy.template.yaml'), 'utf8'));
    settings.Deploy.Git.AutoUpdate = false;
    settings.Deploy.Git.GitExecutable = 'git';
    settings.Deploy.Update.EnableReload = false;
    settings.Deploy.Update.CheckUpdateInterval = 0;
    settings.Deploy.Webui.WebuiHost = '127.0.0.1';
    settings.Deploy.Webui.WebuiPort = await unusedPort();
    fs.writeFileSync(path.join(testRoot, 'config/deploy.yaml'), yaml.stringify(settings));
    fs.mkdirSync(artifacts, {recursive: true});

    app = await electron.launch({
      executablePath: path.join(runtime, 'alas.exe'),
      cwd: os.tmpdir(),
      env: {...environment, ALAS_ROOT: testRoot},
      timeout: 60000,
    });
    appProcessId = await app.evaluate(() => process.pid);
    await waitUntil(() => app.evaluate(async ({BrowserWindow}) => {
      const window = BrowserWindow.getAllWindows()[0];
      if (!window || !window.webContents.getURL()) return false;
      const frame = window.webContents.mainFrame.frames.find(child => child.url.startsWith('http://127.0.0.1:'));
      return frame && frame.executeJavaScript('Boolean(document.querySelector("#pywebio-scope-aside button"))');
    }), 'The packaged desktop did not render the Web UI');
    const content = await app.evaluate(async ({BrowserWindow}) => {
      const frame = BrowserWindow.getAllWindows()[0].webContents.mainFrame.frames[0];
      return frame.executeJavaScript('document.body.innerText');
    });
    assert.ok(content.trim().length > 20, 'Web UI content is empty');
    assert.ok(await app.evaluate(({BrowserWindow}) => BrowserWindow.getAllWindows()[0].isVisible()));
    assert.ok(await responds(settings.Deploy.Webui.WebuiPort));
    const screenshot = await app.evaluate(async ({BrowserWindow}) => {
      const image = await BrowserWindow.getAllWindows()[0].webContents.capturePage();
      return image.toPNG().toString('base64');
    });
    fs.writeFileSync(path.join(artifacts, 'desktop.png'), Buffer.from(screenshot, 'base64'));
    await app.evaluate(({ipcMain}) => ipcMain.emit('window-close'));
    await app.close();
    await waitUntil(() => {
      try {
        process.kill(appProcessId, 0);
        return false;
      } catch (error) {
        if (error.code !== 'ESRCH') throw error;
        return true;
      }
    }, 'Desktop did not close cleanly');
    app = undefined;
    console.log('Packaged desktop: visible window, live Web UI, clean shutdown.');

    settings.Deploy.Webui.WebuiPort = await unusedPort();
    fs.writeFileSync(path.join(testRoot, 'config/deploy.yaml'), yaml.stringify(settings));
    const launcher = spawn(path.join(testRoot, 'Alas.exe'), [], {
      cwd: os.tmpdir(), env: environment, windowsHide: true,
    });
    const exitCode = await new Promise((resolve, reject) => {
      launcher.once('error', reject);
      launcher.once('exit', resolve);
    });
    assert.strictEqual(exitCode, 0, 'Native launcher failed');
    const child = execFileSync('pwsh', ['-NoProfile', '-Command',
      `Get-CimInstance Win32_Process -Filter "ParentProcessId = ${launcher.pid} AND Name = 'alas.exe'" | Select-Object -ExpandProperty ProcessId`],
    {encoding: 'utf8'}).trim();
    nativeProcessId = Number(child);
    assert.ok(nativeProcessId > 0, 'Native launcher did not start the packaged desktop');
    await waitUntil(() => responds(settings.Deploy.Webui.WebuiPort), 'Native launcher did not start the Python backend');
    await waitUntil(() => execFileSync('pwsh', ['-NoProfile', '-Command',
      `(Get-Process -Id ${nativeProcessId}).MainWindowHandle`], {encoding: 'utf8'}).trim() !== '0',
    'Native desktop window is not visible');
    console.log('Native Alas.exe: launched from an unrelated directory; desktop window and dedicated backend are running.');
  } catch (error) {
    console.error('Desktop smoke failure:', error);
    const logDirectory = path.join(testRoot, 'log');
    if (fs.existsSync(logDirectory)) {
      for (const file of fs.readdirSync(logDirectory)) {
        if (file.endsWith('_gui.txt')) console.error(fs.readFileSync(path.join(logDirectory, file), 'utf8').slice(-8000));
      }
    }
    throw error;
  } finally {
    if (app) {
      if (appProcessId) killTree(appProcessId);
      else await app.close();
    }
    if (nativeProcessId) killTree(nativeProcessId);
    assert.strictEqual(path.dirname(testRoot), os.tmpdir());
    assert.ok(path.basename(testRoot).startsWith('alas desktop smoke '));
    const remaining = execFileSync('pwsh', ['-NoProfile', '-Command',
      'Get-CimInstance Win32_Process -Filter "Name = \'python.exe\' OR Name = \'alas.exe\'" | Where-Object { $_.CommandLine -and $_.CommandLine.Contains($env:ALAS_SMOKE_ROOT) } | Select-Object -ExpandProperty ProcessId'],
    {encoding: 'utf8', env: {...process.env, ALAS_SMOKE_ROOT: testRoot}}).trim();
    for (const processId of remaining.split(/\s+/).filter(Boolean)) killTree(Number(processId));
    for (const directory of ['module', 'assets', 'bin', 'campaign', 'deploy', 'submodule', '.venv', 'webapp/dist/win-unpacked']) {
      const link = path.join(testRoot, directory);
      if (fs.existsSync(link) && fs.lstatSync(link).isSymbolicLink()) fs.unlinkSync(link);
    }
    fs.rmSync(testRoot, {recursive: true, force: true, maxRetries: 5});
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
