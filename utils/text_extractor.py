import easyocr

reader = easyocr.Reader(['en'], gpu=False)


def extract_text(image):

    result = reader.readtext(
        image,
        paragraph=False,
        detail=1
    )

    data = []

    for item in result:

        bbox = item[0]
        text = item[1]
        confidence = item[2]

        data.append({
            "text": text,
            "confidence": confidence,
            "bbox": bbox
        })

    return data