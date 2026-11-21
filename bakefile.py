# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "bakefile[lib]>=0.0.84",
# ]
# ///

from typing import ClassVar

from bakelib.space import BaseSpace, SubmodulesUtils


class MyBakebook(SubmodulesUtils, BaseSpace):
    __exclude_command_methods__: ClassVar[list[str]] = [
        "test",
        "test_all",
        "test_integration",
    ]

    def test(self) -> None:
        # assert-setup-dev calls test(); a dotfiles repo has nothing to test
        pass


bakebook = MyBakebook()
