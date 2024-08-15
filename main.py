import os.path
from tkinter import Event, StringVar, BooleanVar
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.constants import *
from tkinter.filedialog import askdirectory, askopenfilename
from functools import partial
from ttkbootstrap.toast import ToastNotification
from PortraitCreator import *
from ParadoxUtils import *


# Create the root tkkbootstrap window
root = ttk.Window(size=(800, 600), themename="darkly")


class UtilityTool(ttk.Frame):
    def __init__(self, master):
        """
        Initialize the UtilityTool class
        :param master: The master widget for this frame
        """
        super().__init__(master)
        self.pack(fill=BOTH)

        title = ttk.Label(master, text="Hearts of Iron 4 Utility Tool", font=("Helvetica", 24, "bold"))
        title.pack(side=TOP, pady=(10, 0))  # Add padding to position the label
        titleUnderscore = ttk.Separator(master)
        titleUnderscore.pack(side=TOP, fill=X, padx=20)

        tabFrame = ttk.Notebook(master, bootstyle="info")
        tabFrame.pack(side=TOP, fill=BOTH, padx=10, pady=10)

        self.tabNames = ["Generate GFX", "Generate Portraits", "Generate Focus Icon", "Generate Generic Characters",
                         "Generate Localisation"]
        self.generateFuncs = [self.generateGFX, self.generatePortraits, self.generateFocusIcon,
                              self.generateGenericCharacters, self.generateLocalisation]

        # List of all the variables used across all the tabs
        # Note: it is clear now that I should have made tabs into their own classes
        self.tabs = []
        self.scrollableFrames = []
        self.inputDirs = [{}, {}, {}, {}, {}]
        self.outputButtons = []
        self.outputErrors = []
        self.filterDirectories = {}
        self.localisationDesiredIdentifiers = {}
        self.referenceVars = {
            "modRoot": StringVar(value="No modroot set"),
            "0": StringVar(value="No output set"),
            "1": StringVar(value="No output set"),
            "2": StringVar(value="No output set"),
            "3": StringVar(value="No output set"),
            "4": StringVar(value="No output set"),
            "focusFrame": StringVar(value="No frame set")
        }
        self.referenceVars["modRoot"].trace("w", self.updateModRoot)
        self.modRootError = ttk.Label()
        self.createAdvisors = BooleanVar(value=False)
        self.focusIconPrefix = StringVar(value="GEN_")
        self.gfxPrefix = StringVar(value="GFX_")
        self.characterPrefix = StringVar(value="GEN_")
        self.characterFileName = StringVar(value="custom_generic_characters.txt")
        self.characterGFXPrefix = StringVar(value="GFX_")

        for i in range(0, len(self.tabNames)):
            newTab = ttk.Frame(tabFrame)
            tabFrame.add(newTab, text=self.tabNames[i])
            self.tabs.append(newTab)
            self.createInputFrame(i)
            buttonMessage = self.createOutputFrame(i)
            self.outputButtons.append(buttonMessage[0])
            self.outputErrors.append(buttonMessage[1])
            self.referenceVars[str(i)].trace("w", partial(self.updateOutputDir, i))

    def createInputFrame(self, tabIndex):
        """
        Create the input frame for a specific tab
        :param tabIndex: The index of the tab for which to create the input frame
        """
        inputFrame = ttk.LabelFrame(self.tabs[tabIndex], text="Input Directory", bootstyle="primary", padding=10)
        inputFrame.pack(side=TOP, pady=5, padx=10, fill=X)

        match tabIndex:
            case 0:
                self.createPathRow(inputFrame, tabIndex, "Add mod directory", "modRoot")
                self.modRootError = ttk.Label(inputFrame, bootstyle="danger")
                self.modRootError.pack(side=TOP, pady=0)
                ttk.Label(inputFrame,
                          text="GFX files use directories relative to the mod directory. The input directory "
                               "must be within the mod directory", bootstyle="warning").pack(side=TOP, pady=5)
            case 2:
                self.createPathRow(inputFrame, tabIndex, "Select PDN focus frame", "focusFrame")
                ttk.Label(inputFrame,
                          text="Input frame must be a .pdn file.\nCharacter images are placed above and "
                               "below the top layer (typically the circular frame of the focus tree "
                               "background).", anchor="center", bootstyle="warning"
                          ).pack(side=TOP, fill=X, expand=YES)

        self.createPathRow(inputFrame, tabIndex, "Add input directory")
        sf = ScrolledFrame(inputFrame, autohide=True, height=100, bootstyle="primary")
        sf.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        self.scrollableFrames.append(sf)

    def createOutputFrame(self, tabIndex):
        """
        Create the output frame for a specific tab
        :param tabIndex: The index of the tab for which to create the output frame
        :return: A tuple containing the output button and the error message label
        """
        outputFrame = ttk.LabelFrame(self.tabs[tabIndex], text="Output Directory", bootstyle="success", padding=10)
        outputFrame.pack(side=TOP, pady=5, padx=10, fill=X)

        warningLabel = ttk.Label(outputFrame,
                                 text="Warning: Make sure all mod files are backed up before generating new files.\n"
                                      "Generated files will overwrite files of the same name in the output directory",
                                 bootstyle="warning")
        warningLabel.pack(
            side=TOP, fill=BOTH, expand=True)
        warningLabel.configure(anchor="center")

        self.createPathRow(outputFrame, tabIndex, "Add output directory", str(tabIndex))
        errorMessage = ttk.Label(outputFrame, bootstyle="danger")
        errorMessage.pack(side=TOP, pady=0)

        outputButton = ttk.Button(outputFrame, text=self.tabNames[tabIndex], bootstyle="primary",
                                  command=self.generateFuncs[tabIndex])
        outputButton.pack(side=LEFT if tabIndex != 3 else TOP, pady=10, padx=10, fill=X, expand=YES)

        match tabIndex:
            case 0:
                UtilityTool.addPrefixEntry(outputFrame, "GFX ID Prefix", self.gfxPrefix)
            case 1:
                ttk.Checkbutton(outputFrame, text="Generate advisor portraits", bootstyle="square-toggle",
                                variable=self.createAdvisors).pack(side=RIGHT, pady=10, padx=10, fill=X)
            case 2:
                UtilityTool.addPrefixEntry(outputFrame, "Focus Image Prefix", self.focusIconPrefix)
            case 3:
                newFrame = ttk.Frame(outputFrame)
                newFrame.pack(side=TOP)
                UtilityTool.addPrefixEntry(newFrame, "Character ID Prefix", self.characterPrefix)
                UtilityTool.addPrefixEntry(newFrame, "Character File Frame", self.characterFileName)
                newFrame2 = ttk.Frame(outputFrame)
                newFrame2.pack(side=TOP)
                UtilityTool.addPrefixEntry(newFrame2, "GFX ID Prefix", self.characterGFXPrefix)

        return outputButton, errorMessage

    def createPathRow(self, frame, tabIndex, label, key=None):
        """
        Add a path row to a label frame
        :param frame: The frame to which the path row is added
        :param tabIndex: The index of the tab for which the path row is created
        :param label: The label for the path row
        :param key: The key for referencing variables. Defaults to None
        """
        pathRow = ttk.Frame(frame)
        pathRow.pack(fill=X, expand=YES, pady=5)
        pathLabel = ttk.Label(pathRow, text=label, width=len(label))
        pathLabel.pack(side=LEFT, padx=(15, 0))
        pathEntry = ttk.Entry(pathRow, textvariable=self.referenceVars[key] if key is not None else "")
        pathEntry.pack(side=LEFT, fill=X, expand=YES, padx=5)

        if key is None:
            pathEntry.bind("<Return>", lambda event: self.onEntryEnter(event, tabIndex))

        browse_btn = ttk.Button(
            master=pathRow,
            text="Browse",
            command=partial(self.handleFolderBrowse, tabIndex, pathEntry, key),
            width=8
        )
        browse_btn.pack(side=LEFT, padx=5)

    def addInputDirToTab(self, tabIndex, directory):
        """
        Add an input directory to a specified tab
        :param tabIndex: The index of the tab to which the directory is added
        :param directory: The directory path to add
        """
        if directory in self.inputDirs[tabIndex]:
            return

        sf = self.scrollableFrames[tabIndex]

        currentFrame = ttk.Frame(sf, bootstyle="dark")
        currentFrame.pack(padx=5, fill=X, expand=YES)

        ttk.Button(currentFrame,
                   text="Remove Path",
                   bootstyle="danger",
                   command=partial(self.deleteInputDirFromTab, tabIndex, directory)
                   ).pack(side=RIGHT, pady=5, padx=(0, 10), fill=X)

        match tabIndex:
            case 1:
                newBool = BooleanVar(value=False)
                ttk.Checkbutton(currentFrame, text="Apply filter", bootstyle="square-toggle", variable=newBool).pack(
                    side=RIGHT, pady=10,
                    padx=10, fill=X)
                self.filterDirectories[directory] = newBool
            case 4:
                useID = BooleanVar(value=True)
                useImages = BooleanVar(value=True)
                useNames = BooleanVar(value=True)
                ttk.Checkbutton(currentFrame, text="IDs", variable=useID).pack(
                    side=RIGHT, pady=10,
                    padx=10, fill=X)
                ttk.Checkbutton(currentFrame, text="Images", variable=useImages).pack(
                    side=RIGHT, pady=10,
                    padx=10, fill=X)
                ttk.Checkbutton(currentFrame, text="Character Names", variable=useNames).pack(
                    side=RIGHT, pady=10,
                    padx=10, fill=X)
                self.localisationDesiredIdentifiers[directory] = (useID, useImages, useNames)

        labelFrame = ttk.Frame(currentFrame)
        labelFrame.pack(side=LEFT, expand=YES, fill=X)
        ttk.Label(labelFrame, text=directory).pack(side=LEFT, padx=5, pady=5)

        self.inputDirs[tabIndex][directory] = currentFrame

    def onEntryEnter(self, event: Event, tabIndex: int):
        """
        Handle the event when an entry widget receives an Enter key press
        :param event: The event object containing information about the key press
        :param tabIndex: The index of the tab where the event occurred
        """
        path = event.widget.get()
        if os.path.exists(path):
            self.addInputDirToTab(tabIndex, path)
        else:
            UtilityTool.displayError("Entered value must be a valid path")

    def deleteInputDirFromTab(self, tabIndex, directory):
        """
        Delete an input directory from a specified tab
        :param tabIndex: The index of the tab from which the directory is deleted
        :param directory: The directory path to delete
        """
        self.inputDirs[tabIndex][directory].destroy()
        self.inputDirs[tabIndex].pop(directory)

        if tabIndex == 1:
            self.filterDirectories.pop(directory)

    def handleFolderBrowse(self, tabIndex, entry, key=None):
        """
        Handle the folder browsing action and update the entry widget
        :param tabIndex: The index of the tab where the browsing occurs
        :param entry: The entry widget to update with the selected path
        :param key: The key for referencing variables. Defaults to None
        """
        path = ""
        if key == "focusFrame":
            path = askopenfilename(filetypes=[("Allowed Types", "*.pdn")])
        else:
            path = askdirectory(title="Select Input Directory")

        if path:
            if key is not None:
                self.referenceVars[key].set(path)
            else:
                self.addInputDirToTab(tabIndex, path)

            UtilityTool.changeEntryContents(entry, path)

    def updateModRoot(self, var, index, mode):
        """
        Update the mod root variable and display an error if the path is invalid
        :param var: The variable being traced
        :param index: The index of the variable
        :param mode: The mode of the trace operation
        """
        self.showErrorIfPathInvalid(self.referenceVars["modRoot"].get(), "ModRoot must be a valid path",
                                    self.modRootError)

    def updateOutputDir(self, realIndex, var, index, mode):
        """
        Update the output directory variable and display an error if the path is invalid
        :param realIndex: The real index of the output directory variable
        :param var: The variable being traced
        :param index: The index of the variable
        :param mode: The mode of the trace operation
        """
        self.showErrorIfPathInvalid(self.referenceVars[str(realIndex)].get(), "Output Directory must be a valid path",
                                    self.outputErrors[realIndex])

    def generateGFX(self):
        """
        Generate GFX files based on input directories and user settings
        :return: True if the GFX generation succeeds, otherwise False
        """
        try:
            for path in self.inputDirs[0]:
                path = self.addEndingSlash(path)
                modPath = self.addEndingSlash(self.referenceVars["modRoot"].get())
                targetPath = self.addEndingSlash(self.referenceVars["0"].get())
                targetFile = self.replaceSlashes(path.replace(modPath, ""), "_")[:-1]

                if not self.checkDirsExist([path, modPath, targetPath]):
                    return False
                else:
                    generateGFXFile(path, modPath, targetPath,
                                    targetFile + ".gfx", UtilityTool.listImageFiles(path), self.gfxPrefix.get())
                    return True
        except:
            print("Generate GFX failed")
            return False

    def generatePortraits(self):
        """
        Generate portraits based on input directories and user settings
        :return: True if the portrait generation succeeds, otherwise False
        """
        try:
            for key in self.inputDirs[1]:
                path = self.addEndingSlash(key)
                targetPath = self.addEndingSlash(self.referenceVars["1"].get())

                if not self.checkDirsExist([path, targetPath]):
                    return False
                else:
                    generatePortraits(path, UtilityTool.listImageFiles(path), self.filterDirectories[key].get(),
                                      targetPath,
                                      self.createAdvisors.get())
        except:
            print("Generate Portraits failed")
            return False

    def generateFocusIcon(self):
        """
        Generate focus icons based on input directories and user settings
        :return: True if the focus icon generation succeeds, otherwise False
        """
        try:
            for key in self.inputDirs[2]:
                path = self.addEndingSlash(key)
                targetPath = self.addEndingSlash(self.referenceVars["2"].get())

                if not self.checkDirsExist([path, targetPath]):
                    return False

                for image in UtilityTool.listImageFiles(path):
                    icon = generateFocusIcon(Image.open(path + image), self.referenceVars["focusFrame"].get())
                    icon.save(targetPath + self.focusIconPrefix.get() + image)

                return True
        except:
            print("Generate focus icon failed")
            return False

    def generateGenericCharacters(self):
        """
        Generate generic characters based on input directories and user settings
        :return: True if the generic character generation succeeds, otherwise False
        """
        try:
            for key in self.inputDirs[3]:
                path = self.addEndingSlash(key)
                targetPath = self.addEndingSlash(self.referenceVars["3"].get())
                targetFile = self.replaceSlashes(self.characterFileName.get(), "_")

                if not self.checkDirsExist([path, targetPath]):
                    return False

                generateGenericCharacters(UtilityTool.listImageFiles(path), targetPath, targetFile)

                return True
        except:
            print("Generate generic characters failed")
            return False

    def generateLocalisation(self):
        """
        Generate localisation files based on input directories and user settings
        :return: True if the localisation file generation succeeds, otherwise False
        """
        try:
            localisationFileNames = {}
            for key in self.inputDirs[4]:
                path = self.addEndingSlash(key)
                targetPath = self.addEndingSlash(self.referenceVars["4"].get())

                if not self.checkDirsExist([path, targetPath]):
                    return False

                finalFolder = os.path.basename(os.path.normpath(path))
                if finalFolder not in localisationFileNames:
                    localisationFileNames[finalFolder] = 1
                else:
                    localisationFileNames[finalFolder] += 1
                    finalFolder += f"{localisationFileNames[finalFolder]}"

                # Remember these are stored as [useID, useImages, useNames]
                useIdentifiers = self.localisationDesiredIdentifiers[key]
                if useIdentifiers[1].get():
                    generateLocalisationFileFromStringList(UtilityTool.listImageFiles(path), targetPath,
                                                           finalFolder + "_l_english.yml")

                identifiers = []
                identifiers.append("id") if useIdentifiers[0] else {}
                identifiers.append("name") if useIdentifiers[2] else {}

                if len(identifiers) > 0:
                    for textFile in listTextFiles(path):
                        with open(path + textFile, "r") as file:
                            generateLocalisationFileFromIdentifiers(file.read(), targetPath,
                                                                    finalFolder + "_l_english.yml", identifiers)
                            file.close()

                return True
        except:
            print("Generate localisation failed")
            return False

    @staticmethod
    def showErrorIfPathInvalid(path, text, label):
        """
        Display an error message on a label if the specified path is invalid
        :param path: The path to check for validity
        :param text: The error message to display if the path is invalid
        :param label: The label widget to update with the error message
        """
        if not os.path.exists(path):
            label.configure(text=text)
        else:
            label.configure(text="")

    @staticmethod
    def addPrefixEntry(master, label, textVariable):
        """
        Add a prefix entry widget to a master widget
        :param master: The master widget to which the entry is added
        :param label: The label for the entry
        :param textVariable: The text variable associated with the entry
        """
        ttk.Entry(master, width=len(textVariable.get()) + 10,
                  textvariable=textVariable).pack(side=RIGHT, pady=10, padx=10, fill=X)
        ttk.Label(master,
                  text=label).pack(side=RIGHT, pady=10, padx=10, fill=X)

    @staticmethod
    def addEndingSlash(path: str):
        """
        Add an ending slash to a path if it does not already have one
        :param path: The path to modify
        :return: The modified path with an ending slash
        """
        if not (path == "/" or path == "\\"):
            path += "/"
        return path

    @staticmethod
    def replaceSlashes(path, character):
        """
        Replace slashes in a path with a specified character
        :param path: The path in which to replace slashes
        :param character: The character to replace slashes with
        :return: The modified path with slashes replaced
        """
        # Replace forward slashes with underscores
        result = path.replace('/', character)
        # Replace backslashes with underscores
        result = result.replace('\\', character)
        return result

    @staticmethod
    def checkDirsExist(paths: [str]):
        """
        Check if all directories in a list of paths exist
        :param paths: A list of directory paths to check
        :return: True if all directories exist, otherwise False
        """
        for path in paths:
            if not os.path.exists(path):
                return False
        return True

    @staticmethod
    def listImageFiles(directory):
        """
        List image files in a specified directory
        :param directory: The directory to search for image files
        :return: A list of image file names in the directory
        """
        # List all files in the directory
        allFiles = os.listdir(directory)

        # Filter for common image file extensions
        imageFiles = [f for f in allFiles if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.dds'))]
        return imageFiles

    @staticmethod
    def displayError(message):
        """
        Display an error message using a toast notification
        :param message: The error message to display
        """
        toast = ToastNotification(
            title="Error",
            message=message,
            duration=3000,  # Duration in milliseconds
            bootstyle="danger"  # Style for error message
        )
        toast.show_toast()

    @staticmethod
    def changeEntryContents(entry, content):
        """
        Change the contents of an entry widget
        :param entry: The entry widget to update
        :param content: The content to insert into the entry widget
        """
        insertFailed = True
        while insertFailed:
            try:
                entry.delete(0, END)
                entry.insert(0, content)
                insertFailed = False
            except:
                print("Caught insert error")
                insertFailed = True


if __name__ == "__main__":
    UtilityTool(root)
    root.mainloop()
