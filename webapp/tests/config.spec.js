const {strict: assert} = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const vm = require('vm');
const ts = require('typescript');

const source = fs.readFileSync(path.join(__dirname, '../packages/main/src/config.ts'), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020},
}).outputText;
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'alas desktop '));
const root = path.join(temporary, 'source with spaces');
const configDirectory = path.join(root, 'config');
const desktop = path.join(root, 'webapp/dist/win-unpacked');
fs.mkdirSync(configDirectory, {recursive: true});
fs.mkdirSync(desktop, {recursive: true});
fs.mkdirSync(path.join(root, '.venv/Scripts'), {recursive: true});
fs.writeFileSync(path.join(root, 'gui.py'), '');
fs.writeFileSync(path.join(root, '.venv/Scripts/python.exe'), '');
fs.writeFileSync(path.join(configDirectory, 'deploy.template.yaml'),
  'Deploy:\n  Python:\n    PythonExecutable: ./toolkit/python.exe\n  Webui:\n    WebuiPort: 22267\n');

function loadConfig(options = {}) {
  const result = {};
  vm.runInNewContext(compiled, {
    exports: result,
    require,
    __dirname: options.bundle || path.join(desktop, 'resources/app.asar/packages/main/dist'),
    process: {
      env: options.env || {},
      execPath: options.executable || path.join(desktop, 'alas.exe'),
      platform: 'win32',
      cwd: () => options.cwd || temporary,
    },
  });
  return result;
}

try {
  const config = loadConfig();
  assert.strictEqual(config.alasPath, root);
  assert.strictEqual(config.pythonPath, path.join(root, '.venv/Scripts/python.exe'));
  assert.ok(fs.existsSync(path.join(configDirectory, 'deploy.yaml')));
  assert.strictEqual(config.webuiUrl, 'http://127.0.0.1:22267');

  const customConfig = 'Deploy:\n  Python:\n    PythonExecutable: ./custom/python.exe\n  Webui:\n    WebuiPort: 23456\n';
  fs.writeFileSync(path.join(configDirectory, 'deploy.yaml'), customConfig);
  assert.strictEqual(loadConfig().pythonPath, path.join(root, 'custom/python.exe'));
  assert.strictEqual(fs.readFileSync(path.join(configDirectory, 'deploy.yaml'), 'utf8'), customConfig);

  const detached = {executable: path.join(temporary, 'installed/alas.exe'), bundle: temporary};
  assert.strictEqual(loadConfig({...detached, env: {ALAS_ROOT: root}}).alasPath, root);
  assert.strictEqual(loadConfig({...detached, cwd: root}).alasPath, root);
  assert.throws(() => loadConfig(detached), /Cannot find Alas sources/);

  fs.unlinkSync(path.join(root, '.venv/Scripts/python.exe'));
  fs.copyFileSync(path.join(configDirectory, 'deploy.template.yaml'), path.join(configDirectory, 'deploy.yaml'));
  assert.strictEqual(loadConfig().pythonPath, path.join(root, 'toolkit/python.exe'));
  console.log('Desktop configuration checks passed.');
} finally {
  fs.rmSync(temporary, {recursive: true, force: true});
}
