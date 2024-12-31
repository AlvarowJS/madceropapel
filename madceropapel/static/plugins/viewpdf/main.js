window.adobe_dc_view_sdk = function (e) {
    var r = {};

    function __webpack_require__(_) {
        if (r[_]) return r[_].exports;
        var n = r[_] = {i: _, l: !1, exports: {}};
        return e[_].call(n.exports, n, n.exports, __webpack_require__), n.l = !0, n.exports
    }

    return __webpack_require__.m = e, __webpack_require__.c = r, __webpack_require__.d = function (e, r, _) {
        __webpack_require__.o(e, r) || Object.defineProperty(e, r, {enumerable: !0, get: _})
    }, __webpack_require__.r = function (e) {
        "undefined" != typeof Symbol && Symbol.toStringTag && Object.defineProperty(e, Symbol.toStringTag, {value: "Module"}), Object.defineProperty(e, "__esModule", {value: !0})
    }, __webpack_require__.t = function (e, r) {
        if (1 & r && (e = __webpack_require__(e)), 8 & r) return e;
        if (4 & r && "object" == typeof e && e && e.__esModule) return e;
        var _ = Object.create(null);
        if (__webpack_require__.r(_), Object.defineProperty(_, "default", {
            enumerable: !0,
            value: e
        }), 2 & r && "string" != typeof e) for (var n in e) __webpack_require__.d(_, n, function (r) {
            return e[r]
        }.bind(null, n));
        return _
    }, __webpack_require__.n = function (e) {
        var r = e && e.__esModule ? function getDefault() {
            return e.default
        } : function getModuleExports() {
            return e
        };
        return __webpack_require__.d(r, "a", r), r
    }, __webpack_require__.o = function (e, r) {
        return Object.prototype.hasOwnProperty.call(e, r)
    }, __webpack_require__.p = "", __webpack_require__(__webpack_require__.s = "c08d")
}({
    c08d: function (e, r) {
        !function () {
            "use strict";
            var e, r, _ = {
                monthly: {version: "2.15.0_2.3.0-e7de4f0"},
                1.5: {version: "2.9.6_1.5.0-0c1a169"},
                "2.0": {version: "2.13.1_2.0.0-9ef32cc"}
            }, n = "monthly", t = document.scripts;
            for (var i in t) t.hasOwnProperty(i) && t[i].src && -1 !== t[i].src.indexOf("view-sdk/main.js") && (e = t[i].src);
            -1 !== e.indexOf("?version=") && (r = e.substring(e.indexOf("?version="), e.length).replace("?version=", ""), Object.keys(_).indexOf(r) > -1 && (n = r), e = e.substring(0, e.indexOf("?version=")));
            var u = e.substring(0, e.indexOf("main.js")) + _[n].version + "/ViewSDKInterface.js",
                c = document.createElement("script");
            c.async = !1, c.setAttribute("src", u), document.head.appendChild(c)
        }()
    }
});
//# sourceMappingURL=2.15.0_2.3.0-99e1ddd/private/main.js.map