from view import App
from model import Model
from presenter import Presenter


def main():
    model = Model()
    app = App()
    presenter = Presenter(model=model, app=app)
    presenter.run()


if __name__ == "__main__":
    main()
