"""Standard Lua built-in globals and functions known to ESO."""

# Standard Lua 5.1 globals (ESO uses Lua 5.1)
LUA_BUILTIN_GLOBALS = {
    "_G", "_VERSION", "arg",
    "assert", "collectgarbage", "dofile", "error",
    "getfenv", "getmetatable", "ipairs", "load",
    "loadfile", "loadstring", "module", "next",
    "pairs", "pcall", "print", "rawequal",
    "rawget", "rawset", "require", "select",
    "setfenv", "setmetatable", "tonumber", "tostring",
    "type", "unpack", "xpcall",
    # ESO disables some, but addons can reference them
    "coroutine", "debug", "io", "math", "os",
    "package", "string", "table",
}

# Standard Lua library functions (keyed by module)
LUA_STDLIB = {
    "string": {
        "byte", "char", "dump", "find", "format", "gmatch", "gsub",
        "len", "lower", "match", "rep", "reverse", "sub", "upper",
    },
    "table": {
        "concat", "insert", "maxn", "remove", "sort",
    },
    "math": {
        "abs", "acos", "asin", "atan", "atan2", "ceil", "cos", "cosh",
        "deg", "exp", "floor", "fmod", "frexp", "ldexp", "log", "log10",
        "max", "min", "modf", "pi", "pow", "rad", "random", "randomseed",
        "sin", "sinh", "sqrt", "tan", "tanh",
    },
    "os": {
        "clock", "date", "difftime", "execute", "exit", "remove",
        "rename", "time", "tmpname",
    },
}

# ESO overridden or extended string functions
ESO_STRING_EXTENSIONS = {
    "string.lowerbybyte", "string.upperbybyte",
}

# ESO zo_* wrappers that override standard lib functions
ESO_ZO_WRAPPERS = {
    "zo_strlower", "zo_strupper",
    "zo_strsub", "zo_strgsub", "zo_strlen", "zo_strmatch",
    "zo_strgmatch", "zo_strfind", "zo_plainstrfind", "zo_strsplit",
    "zo_loadstring",
    "zo_deg", "zo_rad", "zo_floor", "zo_ceil", "zo_mod",
    "zo_decimalsplit", "zo_abs", "zo_max", "zo_min", "zo_sqrt",
    "zo_pow", "zo_cos", "zo_sin", "zo_tan", "zo_atan2",
    "zo_randomseed", "zo_random", "zo_insecureNext", "zo_insecurePairs",
}

# Keywords to ignore (control flow, not function calls)
LUA_KEYWORDS = {
    "and", "break", "do", "else", "elseif", "end",
    "false", "for", "function", "goto", "if", "in",
    "local", "nil", "not", "or", "repeat", "return",
    "then", "true", "until", "while",
}
