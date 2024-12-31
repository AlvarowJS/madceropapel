"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

class ClaseRUC:
    dni = None
    ruc = None

    def __init__(self, dni):
        self.dni = dni
        self.ruc = self.ObtenerRUC(dni)

    def digitoValidador(self):
        _result = None
        if len(self.dni) == 8:
            _contador = 0
            while _contador < 10:
                if self.ValidarRUC('10' + self.dni + str(_contador)):
                    _result = str(_contador)
                    break
                else:
                    _contador += 1
        return _result

    def ObtenerRUC(self, dni):
        if not dni:
            dni = self.dni
        _ruc = ""
        if len(dni) == 8:
            _contador = 0
            while _contador < 10 and len(_ruc) == 0:
                if self.ValidarRUC('10' + dni + str(_contador)):
                    _ruc = '10' + dni + str(_contador)
                    break
                else:
                    _contador += 1
        return _ruc

    def ValidarRUC(self, ruc):
        _correcto = False
        #
        dig01 = int(ruc[0:1]) * 5
        dig02 = int(ruc[1:2]) * 4
        dig03 = int(ruc[2:3]) * 3
        dig04 = int(ruc[3:4]) * 2
        dig05 = int(ruc[4:5]) * 7
        dig06 = int(ruc[5:6]) * 6
        dig07 = int(ruc[6:7]) * 5
        dig08 = int(ruc[7:8]) * 4
        dig09 = int(ruc[8:9]) * 3
        dig10 = int(ruc[9:10]) * 2
        dig11 = int(ruc[10:11]) * 1
        digSuma = dig01 + dig02 + dig03 + dig04 + dig05 + dig06 + dig07 + dig08 + dig09 + dig10
        digResiduo = digSuma % 11
        digResta = 11 - digResiduo
        digChk = (0 if digResta == 10 else (1 if digResta == 11 else digResta))
        _correcto = (dig11 == digChk)
        #
        return _correcto
