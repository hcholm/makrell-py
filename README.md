# Makrell 

<img src="./doc/makrell.png" style="width:10em" />

Makrell is a family of programming languages implemented in Python. It consists currently of these languages:

* **MakrellPy**, a general-purpose programming language with two-way Python compatibility. It features a simple syntax, functional programming constructs and meta programming.
* **MRON** (Makrell Object Notation), a lightweight alternative to JSON.
* **MRML** (Makrell Markup Language), a lightweight alternative to XML and HTML.
* **Makrell Base Format**,  a simple data format that forms the basis for both MakrellPy, MRON and MRML.

## Quick Start

### Installation

```bash
pip install makrell
```

### MakrellPy REPL usage

```bash
makrell
> 2 + 3
5
> [2 3 5] | sum
10
```

### Run a MakrellPy script

```bash
makrell myscript.mr
```

## IDE Support

MakrellPy is supported by the MakrellPy Language Server, included in the Makrell package. The language server is based on the [LSP](https://microsoft.github.io/language-server-protocol/) protocol and can be used with any LSP-compatible editor, such as Visual Studio Code, Sublime Text, Atom, Vim, Emacs etc. A VS Code extension is available [here](https://marketplace.visualstudio.com/items?itemName=hcholm.vscode-makrell).

![VS Code Extension](doc/ide.png)


## MakrellPy

The following is a quick introduction by example to the MakrellPy language. See [examples](examples) and [tests](tests) for more code examples.

### Syntax

MakrellPy uses the Makrell Base Format as its base syntax (see below). MakrellPy-specific syntax is built on top of this. The following is a simple example of a MakrellPy program:

```
# This is a comment.
a = 2
b = a + 3
{sum [a b 5]}  # function call
[a b 5] | sum  # function call through pipe

# Conditional expression
{if a < b
    "a is less than b"
    "a is not less than b"}

# Function definition
{def add [x y]
    x + y}
```

Note:
* The syntax is determined by lists and binary expressions.
* Return values are implicit, i.e. the last expression in a block is the return value.

### Other Features

See the [examples](examples) and [tests](tests) directories for examples of the following features:
* Class definitions
* String interpolation
* Function composition
* Meta programming, including macros, custom operators and embedded mini-languages
* Python interoperability

### TODOs and wishlist

* More built-in functions and operators
* Various missing Python features, such as decorators, yield and async/await
* Basic typing as in Python
* Pattern matching and destructuring
* More advanced typing, possibly unified with basic typing and grammar expressions
* Better error messages and better IDE support
* More documentation and examples
* Transpilers and code generators for other languages   
* Mini-languages for e.g. database queries, regular expressions etc.

## MRON

Example MRON document:

```
owner "Rena Holm"
last_update "2023-11-30"

books [
    {
        title "That Time of the Year Again"
        year 1963
        author "Norton Max"
    }
    {
        title "One for the Team"
        year 2024
        author "Felicia X"
    }
]
```

The above code corresponds to the following Python dictionary tree:

```python
{
    "owner": "Rena Holm",
    "last_update": "2023-11-30",
    "books": [
        {
            "title": "That Time of the Year Again",
            "year": 1963,
            "author": "Norton Max"
        },
        {
            "title": "One for the Team",
            "year": 2024,
            "author": "Felicia X"
        }
    ]
}
```

## MRML

Example MRML document:

```
{html
    {head
        {title A Test}
    }
    {body
        {h1 This is a Test}
        {p [style="color: red"] Just some {b bold} text here.}
    }
}
```

The above code corresponds to the following HTML:

```html
<html>
    <head>
        <title>A Test</title>
    </head>
    <body>
        <h1>This is a Test</h1>
        <p style="color: red">Just some <b>bold</b> text here.</p>
    </body>
</html>
```


## Makrell Base Format

The Makrell Base Format is a simple data format that forms the basis for both MakrellPy, MRON and MRML. It is a simple text-based format that is easy to read and write. It is designed to be easy to parse and generate, and to be easy to work with in a text editor.

These element types are supported:

* **Identifier**: A simple name. Examples:
    * `x`
    * `Y1`
    * `$Example_Æ23`.
* **String**: A sequence of characters surrounded by double quotes. The backslash character is used to escape double quotes and backslashes. A string may have a suffix that specifies an implementation-specific data type. Examples:
    * `"Hi."`
    * `"This is a string: \"Hi.\""`
    * `"2024-02-02"date` : a date
    * `"12AF"hex` : a hexadecimal number
* **Number**: A numeric value. As with strings, a number may have a suffix that specifies an implementation-specific data type or value. Examples:
    * `42`
    * `2.5e9`
    * `2.5G` = 2,500,000,000
    * `2pi` = 6.283185307179586
* **List**: A sequence of elements, surrounded by brackets and usually separated by spaces. Lists may be nested. There are three types of lists:
    * **"Round"**, e.g. `(2 3 5)`
    * **"Square"**, e.g. `["a" "b" "c"]`
    * **"Curly"**, e.g. `{asd qwe zxc}`
* **Operator**: A symbol consisting of one or more non-alphanumeric characters. Examples:
    * `+`
    * `==`
    * `|*`
    * `<*>`

For parsing purposes, the following element types are also defined:

* **Whitespace**: A sequence of space, tab and newline characters.
* **Comment**: A sequence of characters that is ignored by the parser. A line comment starts with a `#` character and continues to the end of the line, while a block comment starts with `/*` and ends with `*/`.
* **Other Token**: A sequence of characters that does not match any of the other element types.

In addition, the following element type is defined in the core library:
* **Binary Expression**: An operator with two operands.

## License

Makrell is developed by Hans-Christian Holm and licensed under the MIT License. See [LICENSE](LICENSE) for details.

