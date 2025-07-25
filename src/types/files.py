from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import ForwardRef


class Function(BaseModel):
    name: str
    arguments: str
    description: str | None

    def to_prompt(self) -> str:
        return f"""
        <Function>
        <Name>{self.name}</Name>
        <Arguments>{self.arguments}</Arguments>
        <Description>{self.description}</Description>
        </Function>
        """


class File(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str | None
    number_of_lines: int
    local_path: str

    imports: List[str] = []
    functions: List[Function] = []

    def to_prompt(self) -> str:
        return f"""
        <File>
        <Name>{self.name}</Name>
        <Description>{self.description}</Description>
        <Imports>{[import_ for import_ in self.imports]}</Imports>
        <Functions>{[function.to_prompt() for function in self.functions]}</Functions>
        </File>
        """


class Repo(BaseModel):
    readme: list[File]
    directories: list[str]
    files: list[File]
    package_files: list[File]

    def to_prompt(self) -> str:
        return f"""
        <Repo>

        <Readme>{[file.to_prompt() for file in self.readme]}</Readme>
        <Directories>{[directory for directory in self.directories]}</Directories>
        <Files>{[file.to_prompt() for file in self.files]}</Files>
        <PackageFiles>{[file.to_prompt() for file in self.package_files]}</PackageFiles>
        </Repo>
        """


# Update forward references
File.model_rebuild()
