const { exec } = require('child_process');
exec('cd "D:\\protofolo projectzzz\\doc for rag\\frontend" && node node_modules\\next\\dist\\bin\\next.js build', (error, stdout, stderr) => {
  if (error) {
    console.error(`exec error: ${error.message}`);
    console.error(stderr);
    process.exit(1);
  }
  console.log(`stdout: ${stdout}`);
  console.error(`stderr: ${stderr}`);
});