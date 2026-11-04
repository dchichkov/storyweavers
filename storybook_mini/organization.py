"""Segment the fixed narrative stream without changing its content or order."""
from dataclasses import dataclass
from .revision import is_dialogue


@dataclass(frozen=True)
class Organized:
    sentence: object
    paragraph: int
    break_reason: str


def organize(sentences, enabled=True, paragraph_sentences=4):
    result, paragraph, length, previous = [], 0, 0, None
    for sentence in sentences:
        c = sentence.clauses[0]
        reason = ""
        if enabled and previous:
            p = previous.clauses[-1]
            if c.scene != p.scene:
                reason = "scene_change"
            elif c.paragraph_break or c.topic != p.topic:
                reason = "topic_change"
            elif is_dialogue(c) and (not is_dialogue(p) or c.subject != p.subject):
                reason = "dialogue_turn"
            elif is_dialogue(p) and c.subject != p.subject:
                reason = "response_action"
            elif length >= paragraph_sentences:
                reason = "paragraph_budget"
        if reason:
            paragraph += 1
            length = 0
        result.append(Organized(sentence, paragraph, reason or ("opening" if not previous else "continue")))
        length += 1
        previous = sentence
    return tuple(result)
