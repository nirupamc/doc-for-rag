const { exec } = require('child_process');
const path = require('path');

// The build script is at frontend/build.js, so node_modules is at frontend/node_modules
const frontendDir = path.resolve(__dirname);

const command = `cd "${frontendDir}" && node node_modules/next/dist/bin/next.js build`;

console.log(`Running build in: ${frontendDir}`);

exec(command, { cwd: frontendDir }, (error, stdout, stderr) => {
  if (error) {
    console.error(`exec error: ${error.message}`);
    console.error(stderr);
    process.exit(1);
  }
  console.log(`stdout: ${stdout}`);
  console.error(stderr);
  console.log('Build completed successfully');
});