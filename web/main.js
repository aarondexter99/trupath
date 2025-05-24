// main.js – loads Pyodide & connects the UI to converter.py
let pyReady = loadPyodide({ indexURL: "pyodide/" }).then(async (py) => {
  // 1) load core packages + micropip
  await py.loadPackage(["pandas", "numpy", "micropip"]);

  // 2) install Excel wheels
  await py.runPythonAsync(`
import micropip
await micropip.install(["openpyxl", "xlrd"])
`);

  // 3) fetch converter.py text
  const converterCode = await (await fetch("converter.py")).text();
  // 4) write it into Pyodide's filesystem
  py.FS.writeFile("converter.py", converterCode);

  // 5) import the module so it's available
  await py.runPythonAsync(`
import converter
`);

  document.getElementById("status").textContent = "Pyodide ready ✔";
  document.getElementById("convert").disabled = false;
  return py;
});

document.getElementById("convert").addEventListener("click", async () => {
  const fileInput = document.getElementById("file");
  if (!fileInput.files.length) {
    alert("Please choose an Excel file first.");
    return;
  }
  const file = fileInput.files[0];
  const buffer = await file.arrayBuffer();
  const py = await pyReady;

  // 6) write the workbook bytes into Pyodide FS
  py.FS.writeFile("workbook.bin", new Uint8Array(buffer));

  // 7) call the converter and get back a base64 ZIP
  const b64 = await py.runPythonAsync(`
import base64, converter
data = open("workbook.bin","rb").read()
base64.b64encode(converter.convert_workbook(data)).decode()
`);
  // 8) build a ZIP blob and trigger download
  const zip = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  const blob = new Blob([zip], { type: "application/zip" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = file.name.replace(/\.(xlsx?|xls)$/i, "_csv.zip");
  a.click();
  URL.revokeObjectURL(a.href);
});
