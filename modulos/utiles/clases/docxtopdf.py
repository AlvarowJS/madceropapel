"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import os
import subprocess


class DocxToPdf:
    system = "win"

    def __init__(self, input, output):
        if os.name != "nt":
            self.system = "linux"
        self.input = input
        self.output = output

    def convert(self):
        if self.system == "win":
            worddoc = None
            wordapp = None
            try:
                from comtypes import client
                wordapp = client.CreateObject('Word.Application')
                worddoc = wordapp.Documents.Open(self.input)
                worddoc.SaveAs(self.output, FileFormat=17)
            except Exception:
                raise
            finally:
                if worddoc:
                    worddoc.Close()
                if wordapp:
                    wordapp.Quit()
        else:
            filelog, ext = os.path.splitext(self.input)
            streamFL = open(filelog + ".txt", "w+")
            try:
                streamFL.write("Convertimos\n")
                cmd = 'unoconv -f pdf'.split() + [self.input]
                streamFL.write(str(cmd) + "\n")
                streamFL.write("Creamos el sub proceso\n")
                p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                streamFL.write("Esperamos\n")
                p.wait(timeout=10)
                streamFL.write("Ejecutamos\n")
                stdout, stderr = p.communicate()
                streamFL.write("Terminado\n")
                if stderr:
                    # streamFL.write(stderr)
                    streamFL.write(subprocess.SubprocessError(stderr).args.__str__())
                    streamFL.write(subprocess.SubprocessError(stderr).__str__())
                    streamFL.write("\n")
                    # raise subprocess.SubprocessError(stderr)
            except Exception as e:
                streamFL.write("Error: " + str(e))
            streamFL.close()

    def convertall(self):
        if self.system == "win":
            wordapp = None
            try:
                from comtypes import client
                wordapp = client.CreateObject('Word.Application')
                for file in os.listdir(self.input):
                    if file.lower().endswith(".docx"):
                        pre, ext = os.path.splitext(file)
                        filedoc = os.path.join(self.input, file)
                        filepdf = os.path.join(self.input, "%s.pdf" % pre)
                        worddoc = wordapp.Documents.Open(filedoc)
                        worddoc.SaveAs(filepdf, FileFormat=17)
                        worddoc.Close(SaveChanges=0)
            except Exception:
                raise
            finally:
                if wordapp:
                    wordapp.Quit()
        else:
            filelog = os.path.join(self.input, "log.txt")
            streamFL = open(filelog, "w+")
            try:
                for file in os.listdir(self.input):
                    if file.lower().endswith(".docx"):
                        cmd = 'unoconv -f pdf'.split() + [os.path.join(self.input, file)]
                        p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                        streamFL.write("Esperamos\n")
                        p.wait(timeout=10)
                        streamFL.write("Ejecutamos\n")
                        stdout, stderr = p.communicate()
                        streamFL.write("Terminado\n")
                        if stderr:
                            # streamFL.write(stderr)
                            streamFL.write(subprocess.SubprocessError(stderr).args.__str__())
                            streamFL.write(subprocess.SubprocessError(stderr).__str__())
                            streamFL.write("\n")
                            # raise subprocess.SubprocessError(stderr)
            except Exception as e:
                streamFL.write("Error: " + str(e))
            streamFL.close()
