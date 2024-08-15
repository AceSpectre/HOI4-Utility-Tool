from PIL import Image, ImageFilter
import cv2
import numpy as np
import pypdn


def transformImage(image: Image, corners: []):
    """
    Transforms an image so its four corners match the provided four corners
    :param image: Image to transform
    :param corners: Corners to transform the image to
    :return: Transformed image
    """
    # Define the transformation matrix using four corners
    sourceCorners = np.float32([[0, 0], [image.shape[1], 0], [0, image.shape[0]], [image.shape[1], image.shape[0]]])
    transformationMatrix = cv2.getPerspectiveTransform(sourceCorners, corners)

    # Determine the dimensions of the transformed image
    transformedCorners = cv2.perspectiveTransform(np.array([sourceCorners]), transformationMatrix)[0]
    max_x, max_y = np.max(transformedCorners, axis=0)
    width, height = int(max_x), int(max_y)

    # Create an output image with an alpha channel
    outputImage = np.zeros((67, 65, 4), dtype=np.uint8)

    # Apply the transformation and set alpha values
    outputImage[:, :, 3] = 0  # Set alpha channel to fully transparent within the transformed region

    transformed = cv2.warpPerspective(image, transformationMatrix, (width, height))
    outputImage[:transformed.shape[0], :transformed.shape[1], :3] = transformed
    outputImage[:transformed.shape[0], :transformed.shape[1], 3] = 255
    return outputImage


def createMaskFromAlpha(image: np.array):
    """
    Creates a mask using the alpha values of Image pixels
    :param image: Image to create a mask from
    :return: An image mask
    """
    mask = np.full((image.shape[0], image.shape[1]), 0, dtype=np.uint8)
    for x in range(image.shape[0]):
        for y in range(image.shape[1]):
            # Using index 3 causes a runtime error if the provided image is not RGBA,
            # if this causes a crash, set every pixel to 0
            try:
                mask[x, y] = 255 - image[x, y, 3]
            except:
                mask[x, y] = 0
    return mask


def createMaskFromBlack(image: np.array):
    """
    Creates an image mask from black areas of an image
    :param image: Image to create a mask from
    :return: An image mask
    """
    mask = np.full((image.shape[0], image.shape[1]), 255, dtype=np.uint8)
    for x in range(image.shape[0]):
        for y in range(image.shape[1]):
            if image[x, y].all() == 0:
                mask[x, y] = 0
    return mask


def addMask(originalMask: np.array, newMask: np.array):
    """
    Combines two image masks, masks out pixels in originalMask if their corresponding pixel in newMask is masked out
    :param originalMask: Mask to update
    :param newMask: Mask to add to the original mask
    :return: Updated mask
    """
    for x in range(originalMask.shape[0]):
        for y in range(originalMask.shape[1]):
            if newMask[x, y].all() == 0:
                originalMask[x, y] = 0
    return originalMask


def invertMask(mask: np.array):
    """
    Inverts a mask matrix, setting each pixel to: 255 - currentPixel
    :param mask: Mask matrix
    :return: Inverted mask matrix
    """
    for x in range(mask.shape[0]):
        for y in range(mask.shape[1]):
            mask[x, y] = 255 - mask[x, y]
    return mask


def targetXDownscale(image: Image, targetX: int):
    """
    Downscales an image to a target X length in pixels while maintaining the image's aspect ratio
    :param image: Image to downscale
    :param targetX: Target X length in pixels
    :return: Downscaled image
    """
    downFactor = image.size[0] / targetX
    image2 = image.resize((targetX, int(image.size[1] / downFactor)))
    return image2


def generateAdvisorPortrait(inputImage: Image):
    """
    Generates an advisor portrait for a given input image
    :param inputImage: Image to transform into the frame of the advisor portrait
    :return: The input image transformed inside the advisor portrait
    """
    portraitBase = Image.open("Assets/Minister Base.png")
    inputImageArray = np.array(inputImage)
    targetCorners = np.float32([[5, 8], [40, 5], [9, 57], [44, 54]])
    inputImageTransformed = Image.fromarray(transformImage(inputImageArray, targetCorners))

    inputMask = createMaskFromBlack(np.array(inputImageTransformed))
    portraitMask = createMaskFromAlpha(np.array(portraitBase))
    collatedMasks = addMask(portraitMask, inputMask)
    collatedMasks = invertMask(collatedMasks)

    inputImageTransformed.paste(portraitBase, (0, 0), Image.fromarray(collatedMasks))
    return inputImageTransformed


def createPortrait(inputImage: Image, filterImage: bool = True):
    """
    Takes an image of a character without a background, de-noises and sharpens the image
    and places the image over a HOI4 character portrait background
    :param inputImage: Image of the character to place on a HOI4 leader background
    :param filterImage: If true, image is filtered
    :return: 156x210 character portrait image
    """
    inputImage = targetXDownscale(inputImage, 156)
    leaderMask = createMaskFromAlpha(np.array(inputImage))
    leaderMask = invertMask(leaderMask)
    portraitBase = Image.open("Assets/Leader Background.png")
    portraitBase.paste(inputImage, (0, 0), Image.fromarray(leaderMask))

    if filterImage:
        portraitBase = portraitBase.filter(ImageFilter.MedianFilter(3))
        portraitBase = portraitBase.filter(ImageFilter.SHARPEN())

    return portraitBase


def generatePortraits(sourceDir: str, folder: [str], filterImages: bool, outputDir: str, genAdvisors: bool = True):
    """
    Generates portraits from a list of image files in a source directory
    :param sourceDir: Input folder path
    :param folder: List of images within the input folder
    :param filterImages: Whether to apply a median filter and sharpen to the input images
    :param outputDir: Output folder path
    :param genAdvisors: Whether to generate advisor portraits from the input images additionally
    """
    for f in folder:
        currentImage = Image.open(sourceDir + f)
        largePortrait = createPortrait(currentImage, filterImages)

        largeImagePath = outputDir + f
        largePortrait.save(largeImagePath)

        if genAdvisors:
            smallImagePath = outputDir + "small_" + f
            generateAdvisorPortrait(largePortrait).save(smallImagePath)


def generateFocusIcon(baseImage: Image, pdnFramePath: str):
    """
    Places the bottom half of a HOI4 character image below the top layer of a PDN file and the top half above the
    top layer
    :param baseImage: Image to place within the focus icon
    :param pdnFramePath: Path to the PDN focus icon frame
    :return: Flattened image with the baseImage layered beneath and above the frame
    """
    # Open PDN image and downscale/convert the image of the character
    layeredImage = pypdn.read(pdnFramePath)
    characterImage = targetXDownscale(baseImage.convert("RGBA"), 65)

    # Convert the image to a numpy array before flattening
    for layer in layeredImage.layers:
        layer.image = np.array(layer.image).astype(np.float32)
    maskImage = Image.fromarray(np.array(layeredImage.flatten(asByte=True)))

    layerBottom = Image.new("RGBA", (100, 88), (0, 0, 0, 0))
    layerTop = layerBottom.copy()

    # Crop the top half of the input image and place it within the topHalf image
    topHalf = characterImage.crop((0, 0, characterImage.width, characterImage.height // 2))
    layerTop.paste(topHalf, (19, -3), topHalf)

    # Crop the bottom half of the input image and place it within the bottomHalf image
    bottomHalf = characterImage.crop((0, characterImage.height // 2, characterImage.width, characterImage.height))
    bottomHalfFull = layerBottom.copy()
    bottomHalfFull.paste(bottomHalf, (19, 40), bottomHalf)
    layerBottom.paste(bottomHalfFull, (0, 0), maskImage)

    # Create new PDN layers from the top and bottom half images
    pdBottomLayer = pypdn.Layer(
        name="",
        image=layerBottom,
        opacity=255,
        blendMode=pypdn.BlendType.Normal,
        visible=True,
        isBackground=False,
    )
    pdTopLayer = pypdn.Layer(
        name="",
        image=layerTop,
        opacity=255,
        blendMode=pypdn.BlendType.Normal,
        visible=True,
        isBackground=False,
    )

    # Place the PDN layers into the PDN focus frame
    layeredImage.layers.insert(len(layeredImage.layers) - 1, pdBottomLayer)
    layeredImage.layers.append(pdTopLayer)

    # Convert the image to a numpy array before flattening
    for layer in layeredImage.layers:
        layer.image = np.array(layer.image).astype(np.float32)
    flattenedImage = layeredImage.flatten(asByte=True)

    # Return the flattened image
    return Image.fromarray(np.array(flattenedImage))
