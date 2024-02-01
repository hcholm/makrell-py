import importlib
_mr_macros_ = {"asd": "asd"}

m12435 = importlib.import_module("makrell.mron")
# print("_mr_macros_:", m._mr_macros_)
names123 = m12435.a, m12435.mronm
print(names123)
for n in names123:
    if hasattr(n, "_mr_macro_"):
        print("has macro", n)
    else:
        print("no macro", n)

# m.mronm("asd")

#import makrell.mron


#print(makrell.mron._mr_macros_)

#print(_mr_macros_)

#f = makrell.mron.mronm
# print decorators
#print(f.__dict__)

# # {import makrell.mron@[_mr_macros_]}
# {import makrell.mron}

# {print _mr_macros_}
# # {print makrell.mron._mr_macros_}

# {*
# books = {mron
#     owner "Rena Holm"
#     last_update "2023-11-30"

#     books [
#         {
#             title "That Time of the Year Again"
#             year 1963
#             author "Norton Max"
#         }
#         {
#             title "One for the Team"
#             year 2024
#             author "Felicia X"
#         }
#     ]
# }

# {print books.owner*}
