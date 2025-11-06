import re

def format_markdown(text):
    # ***text*** → <b><i>text</i></b>
    text = re.sub(r"\*\*\*(.*?)\*\*\*", r"<b><i>\1</i></b>", text)

    # **text** → <b>text</b>
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)

    # *text* → <i>text</i>
    text = re.sub(r"(?<!\*)\*(?!\*)(.*?)\*(?<!\*)", r"<i>\1</i>", text)

    # Xuống dòng: nếu Gemini trả về "\n", chuyển thành <br>
    text = text.replace("\n", "<br>")

    return text

print(format_markdown("""Chắc chắn rồi, đây là một vài ví dụ thực tế về cách sử dụng "in fact":

**1. Để nhấn mạnh hoặc làm rõ một điều gì đó:**

*   **Tình huống:** Bạn nghĩ rằng một người bạn chỉ hơi mệt mỏi.
*   **Câu nói:** "I thought she was just tired, but **in fact**, she's been feeling ill for weeks." (Tôi cứ tưởng cô ấy chỉ mệt thôi, nhưng **thực tế là**, cô ấy đã cảm thấy không khỏe trong nhiều tuần rồi.)

**2. Để đưa ra thông tin trái ngược hoặc bất ngờ:**

*   **Tình huống:** Mọi người nghĩ rằng việc học một ngôn ngữ mới rất khó.
*   **Câu nói:** "Many people think learning a new language is difficult, but **in fact**, with the right resources and motivation, it can be quite enjoyable." (Nhiều người nghĩ rằng học một ngôn ngữ mới là khó, nhưng **thực tế là**, với tài liệu và động lực phù hợp, nó có thể khá thú vị.)

**3. Để thêm thông tin chi tiết hoặc cụ thể hơn:**

*   **Tình huống:** Bạn đang nói về một bộ phim.
*   **Câu nói:** "The movie was good, **in fact**, it was one of the best I've seen this year." (Bộ phim hay, **thực tế là**, nó là một trong những bộ phim hay nhất tôi đã xem năm nay.)

**4. Để sửa chữa hoặc điều chỉnh một phát biểu trước đó:**

*   **Tình huống:** Bạn không chắc chắn về số lượng chính xác.
*   **Câu nói:** "I think there were about twenty people at the party, **in fact**, there were probably closer to thirty." (Tôi nghĩ có khoảng hai mươi người ở bữa tiệc, **thực tế là**, có lẽ gần ba mươi người hơn.)

**Tóm lại, "in fact" được sử dụng để:**

*   Nhấn mạnh sự thật
*   Đưa ra thông tin trái ngược
*   Thêm chi tiết
*   Sửa chữa thông tin

Hy vọng điều này giúp bạn hiểu rõ hơn về cách sử dụng "in fact" trong thực tế!..."""))