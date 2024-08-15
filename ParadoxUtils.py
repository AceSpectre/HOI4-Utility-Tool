import json
import os
import re


def safeWriteToFile(filePath: str, content, encoding: str = "utf-8"):
    """
    Writes to a file using the provided encoding within a try-except
    :param filePath: Path to the file
    :param content: Content of the file
    :param encoding: Encoding of the file, defaults to "utf-8"
    """
    try:
        with open(filePath, 'w', encoding=encoding) as newFile:
            newFile.write(content)
            newFile.close()
    except:
        print("Write to file failed")


def generateGFXFile(sourceDir: str, modDir: str, targetDir: str, targetFileName: str, images: [str],
                    namePrefix: str = "GFX_"):
    """
    Generates a GFX file for all the image files within the provided directory and saves it to a target file
    :param sourceDir: Directory containing input images
    :param modDir: Directory for the root of the mod
    :param targetDir: Directory to save the GFX file to
    :param targetFileName: Name of the new GFX file
    :param images: List of images within the input directory
    :param namePrefix: Prefix to add to names of the sprite types
    """
    interface = {"spriteTypes": {}}

    for i in range(0, len(images)):
        interface["spriteTypes"].update({
            f"spriteType{i}": {
                "name": namePrefix + images[i].split('.', 1)[0],
                "texturefile": sourceDir.replace(modDir, "") + images[i]
            },
        })

    os.makedirs(targetDir, exist_ok=True)

    jsonString = json.dumps(interface, indent=4)
    fixedJson = jsonStringToParadoxText(jsonString, "spriteType", ["spriteTypes", "spriteType", "name", "texturefile"])

    safeWriteToFile(targetDir + targetFileName, fixedJson)


def jsonStringToParadoxText(content: str, indexedPattern: str, removeQuotePattern: [str]):
    """
    Converts a json string to a paradox compatible string
    :param content: JSON string
    :param indexedPattern: String that was repeated during creation of the dictionary and had an index appended to it
    :param removeQuotePattern: String that needs to appear in the paradox file without surrounding "double quotes"
    :return: Paradox compatible string
    """
    fixedJson = re.sub(fr"{indexedPattern}\d+", indexedPattern, content)
    fixedJson = fixedJson.replace(",", "")
    fixedJson = fixedJson.replace(":", "=")
    fixedJson = fixedJson[1:-1]

    for pattern in removeQuotePattern:
        fixedJson = re.sub(fr"\"{pattern}\"", pattern, fixedJson)

    return fixedJson


def generateLocalisationFileFromStringList(characters: [str], targetDir: str, targetFileName: str):
    """
    Generates and saves an english localisation file that provides localisation for keys matching a provided list of strings
    :param characters: List of strings to provide localisations for
    :param targetDir: Output directory
    :param targetFileName: Output file name
    """
    localisationContent = "l_english:"

    for i in range(0, len(characters)):
        characters[i] = characters[i].split('.', 1)[0]
        localisationContent += f"\n {characters[i].lower()}: \"{characters[i].lower()}\" "

    os.makedirs(targetDir, exist_ok=True)

    safeWriteToFile(targetDir + targetFileName, localisationContent, "utf-8-sig")


def generateLocalisationFileFromIdentifiers(sourceFile: str, targetDir: str, targetFileName: str,
                                            identifierNames: [str] = None):
    """
    Generates and saves an english localisation file that provides localisation for keys declared using the provided
    identifierNames (such as "id", or "name")
    :param sourceFile: Input directory of paradox *.txt files
    :param targetDir: Output directory
    :param targetFileName: Output file name
    :param identifierNames: Identifiers to pull localisation keys from
    """
    if identifierNames is None:
        identifierNames = ["id"]

    localisationContent = "l_english:"
    for currentID in identifierNames:
        pattern = fr'{currentID}\s*=\s*([^\n\r]*)'

        ids = re.findall(pattern, sourceFile)

        for i in range(0, len(ids)):
            localisationContent += f"\n {ids[i]}:{'0' if currentID == 'id' else ''} \"{removeUnderscoresCapitalise(ids[i])}\" "

    if localisationContent != "l_english:":
        os.makedirs(targetDir, exist_ok=True)
        safeWriteToFile(targetDir + targetFileName, localisationContent, "utf-8-sig")


def removeUnderscoresCapitalise(s: str):
    """
    Removes all underscores from a string and capitalise characters following underscores (and the first character)
    :param s: String to modify
    :return: Modified string
    """
    # Remove any number of capital letters followed by an underscore
    s = re.sub(r'[A-Z]+_', '', s)

    # Convert the string to a list of characters for easier manipulation
    chars = list(s)

    # Iterate through the list of characters
    for i in range(len(chars)):
        if i == 0:
            chars[0] = chars[0].upper()

        if chars[i] == '_':
            # Replace underscore with space
            chars[i] = ' '
            # Capitalize the next character if it exists
            if i + 1 < len(chars) and chars[i + 1].isalpha():
                chars[i + 1] = chars[i + 1].upper()

    # Join the list back into a string
    return ''.join(chars)


def generateGenericCharacters(characters: [str], targetDir: str, targetFileName: str,
                              namePrefix: str = "GEN_", gfxPrefix: str = "GFX_"):
    """
    Generates and saves a file of generic characters, created from a list of input strings
    :param characters: List of names of the characters (used for name= and for other values with prefixes)
    :param targetDir: Output directory
    :param targetFileName: Output file name
    :param namePrefix: Prefix used for the token_base
    :param gfxPrefix: Prefix used for references to GFX sprite types
    """
    everyCountry = {"every_possible_country": {}}
    everyCountry["every_possible_country"].update({"limit": {}})

    for i in range(0, len(characters)):
        characters[i] = characters[i].split('.', 1)[0]

    for i in range(0, len(characters)):
        everyCountry["every_possible_country"].update({
            f"generate_character{i}": {
                "token_base": namePrefix + characters[i].lower(),
                "name": characters[i].lower(),
                "portraits": {
                    "army": {
                        "large": gfxPrefix + characters[i].lower()
                    },
                    "civilian": {
                        "large": gfxPrefix + characters[i].lower(),
                        "small": gfxPrefix + "small_" + characters[i].lower(),
                    },
                    "navy": {
                        "large": gfxPrefix + characters[i].lower(),
                    }
                },
                "advisor": {
                    "slot": "political_advisor",
                    "traits": {
                    }
                },
            }
        })

    os.makedirs(targetDir, exist_ok=True)

    jsonString = json.dumps(everyCountry, indent=4)
    fixedJson = jsonStringToParadoxText(jsonString, "generate_character", [])
    fixedJson = fixedJson.replace("\"", "")

    safeWriteToFile(targetDir + targetFileName, fixedJson)


def addSharedFocusToEveryTree(inputDir: str, sharedFocus: str):
    """
    Adds a shared focus to every focus tree in the provided directory
    :param inputDir: Input directory
    :param sharedFocus: Name of the (first) shared focus to add to every tree
    """
    focusTrees = listTextFiles(inputDir)

    for currentTree in focusTrees:
        with open(inputDir + currentTree, "r+", encoding="utf-8") as file:
            oldTree = file.read()
            print(oldTree)
            pattern = r"(focus_tree\s*=\s*\{)"

            if re.search(pattern, oldTree):
                newTree = re.sub(pattern, r"\1" + "shared_focus = " + sharedFocus, oldTree, count=1)
                file.seek(0)
                file.write(newTree)
                file.truncate()


def listTextFiles(directory):
    """
    List text files in a specified directory
    :param directory: The directory to search for text files
    :return: A list of text file names in the directory
    """
    # List all files in the directory
    allFiles = os.listdir(directory)

    # Filter for text files
    textFiles = [f for f in allFiles if f.lower().endswith('.txt')]
    return textFiles

