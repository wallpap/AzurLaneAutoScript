const yaml = require('yaml');
const fs = require('fs');
const path = require('path');

const candidates = [process.env.ALAS_ROOT, path.dirname(process.execPath), __dirname, process.cwd()];
let projectRoot: string | undefined;
for (const candidate of candidates) {
  if (!candidate) continue;
  let directory = path.resolve(candidate);
  while (!projectRoot) {
    if (fs.existsSync(path.join(directory, 'gui.py')) && fs.existsSync(path.join(directory, 'config/deploy.template.yaml'))) {
      projectRoot = directory;
      break;
    }
    const parent = path.dirname(directory);
    if (parent === directory) break;
    directory = parent;
  }
  if (projectRoot) break;
}
if (!projectRoot) throw new Error('Cannot find Alas sources. Extract the desktop package into the Alas project folder.');
export const alasPath = projectRoot;

const configPath = path.join(alasPath, 'config/deploy.yaml');
if (!fs.existsSync(configPath)) {
  fs.copyFileSync(path.join(alasPath, 'config/deploy.template.yaml'), configPath);
}

const file = fs.readFileSync(configPath, 'utf8');
const config = yaml.parse(file);
const PythonExecutable = config.Deploy.Python.PythonExecutable;
const WebuiPort = config.Deploy.Webui.WebuiPort.toString();
const configuredPython = path.resolve(alasPath, PythonExecutable);
const legacyPython = path.join(alasPath, 'toolkit', 'python.exe');
const projectPython = path.join(alasPath, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');

export const pythonPath = configuredPython === legacyPython && fs.existsSync(projectPython)
  ? projectPython
  : configuredPython;
export const webuiUrl = `http://127.0.0.1:${WebuiPort}`;
export const webuiPath = 'gui.py';
export const webuiArgs = ['--port', WebuiPort, '--electron'];
export const dpiScaling = Boolean(config.Deploy.Webui.DpiScaling) || (config.Deploy.Webui.DpiScaling === undefined) ;
