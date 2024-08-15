# HOI4-Utility-Tool
A utility tool for Hearts of Iron IV Modding

## Features
### Generate GFX files

GFX files can be automatically generated from folders of images, removing any need for redundant work

### Generate Character Portraits

- HOI4 character backgrounds can be added to characters with transparent backgrounds
- Advisor portraits can be automatically created from images of characters

### Generate Focus Icons

Character images can be automatically placed above/below a focus frame in .pdn to create a national focus of that character

### Generate Generic Characters

Generic characters can be created from a folder of images

### Generate English Localisation Files

English localisation files can be created using any of the following as localisation keys
- `id=` lines within .txt files, such as focus trees
- `name=` lines within .txt files, such as character files
- Names of image files within a folder

Default localisation text removes the underscores and capitalises the first letter of each word
- For example: `recruit_ryan_gosling` becomes `"Recruit Ryan Gosling"`