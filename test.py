
class Story:
    def __init__(self, func):
        self.func = func
        self.id = func.__name__
        print(f"Directory of func: {dir(func)}")
        print(f"Globals of func: {func.__globals__.keys()}")
        print(f"Closure of func: {func.__closure__}")

    
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
    
    def __repr__(self):
        return f"Story({self.id})"
    
    def __getattr__(self, name):
        """Allow to access a registered story as an attribute."""
        return Stories.__getattribute__(name)

def Stories():
    def decorator(func):
        story = Story(func)
        Stories.__setattr__(func.__name__, story)
        return story
    return decorator


def test():

    @Stories()
    def Test():
        print("Inside Test, Test is:", Test)
        return "123 Test Story 123"

    @Stories()
    def Brave():
        print("Inside Brave, Brave is:", Brave)
        print("Type:", type(Brave))
        print("Can access .id:", Brave.id)
        print("Calling Test() inside Brave", Brave.Test())
        print("Calling Test1() inside Brave", Brave.Test1())

    print("Before calling, Brave is:", Brave)
    print("Type:", type(Brave))
    print("\nCalling Brave():")
    Brave()

    print("\n" + "="*50)
    print("SUCCESS! The global Brave resolves to the Story object")
    print("="*50)


if __name__ == "__main__":
    test()