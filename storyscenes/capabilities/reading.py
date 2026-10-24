"""Reader-only evidence and focused follow-ups, independent of simulator truth.

Realizers produce atomic supported statements and their exact text spans. The
reader receives only selected statements, never a world state or hidden trace.
Free authored flourishes carry no inferred facts. This boundary is deliberately
not an English entailment checker: realization templates need semantic review.
"""
from dataclasses import dataclass

from .core import CapabilityError


@dataclass(frozen=True, kw_only=True)
class Statement:
    id: str
    text: str
    kind: str
    focus: str
    answer: str
    event_ids: tuple[str, ...]
    entity_ids: tuple[str, ...] = ()
    reference_tick: int | None = None
    acquired_tick: int | None = None
    needs: tuple[str, ...] = ()
    question: str = ""
    paragraph: str = ""


@dataclass(frozen=True, kw_only=True)
class Answer:
    question: str
    answer: str
    supported: bool
    statement_ids: tuple[str, ...] = ()
    event_ids: tuple[str, ...] = ()
    entity_ids: tuple[str, ...] = ()
    reference_tick: int | None = None


@dataclass(frozen=True, kw_only=True)
class Document:
    title: str
    statements: tuple[Statement, ...]

    def __post_init__(self):
        ids = [s.id for s in self.statements]
        if len(ids) != len(set(ids)) or any(not s.id or not s.text.strip() for s in self.statements):
            raise CapabilityError("Narrative statements need unique IDs and text")
        for statement in self.statements:
            if statement.answer and not statement.event_ids:
                raise CapabilityError("Reading assertions need identified event/premise support")

    @property
    def story(self):
        return "".join(separator + s.text for separator, s in self.layout())

    def layout(self):
        previous = None
        for statement in self.statements:
            separator = "" if previous is None else (
                " " if statement.paragraph and statement.paragraph == previous.paragraph else "\n\n")
            yield separator, statement
            previous = statement

    def mask(self, statement_ids):
        """Remove text and its support together; never leave invisible annotations."""
        hidden = set(statement_ids)
        return Document(title=self.title, statements=tuple(s for s in self.statements if s.id not in hidden))

    def spans(self):
        offset = 0
        spans = []
        for separator, statement in self.layout():
            offset += len(separator)
            spans.append(dict(id=statement.id, start=offset, end=offset + len(statement.text),
                              event_ids=statement.event_ids, entity_ids=statement.entity_ids,
                              reference_tick=statement.reference_tick))
            offset += len(statement.text)
        return spans


class Reader:
    def __init__(self, document):
        self.document = document
        self.last = None
        self.last_event = None

    def support(self, statement):
        by_id = {s.id: s for s in self.document.statements}
        pending, seen = [statement.id], set()
        while pending:
            sid = pending.pop()
            if sid in seen:
                continue
            if sid not in by_id:
                return None
            seen.add(sid)
            pending.extend(by_id[sid].needs)
        return tuple(s for s in self.document.statements if s.id in seen)

    def ask(self, kind, focus, *, event_id=None, reference_tick=None, question=None):
        prompt = question or f"{kind}: {focus}?"
        candidates = [s for s in self.document.statements if s.kind == kind and s.focus == focus and s.answer
                      and (event_id is None or event_id in s.event_ids)
                      and (reference_tick is None or s.reference_tick == reference_tick)]
        # A focus with several temporal statements needs an explicit event/time.
        if len(candidates) != 1:
            self.last = None
            return Answer(question=prompt, answer="The story does not establish that.", supported=False)
        statement = candidates[0]
        support = self.support(statement)
        if support is None:
            self.last = None
            return Answer(question=prompt, answer="The story does not establish that.", supported=False)
        self.last = statement
        self.last_event = event_id or (statement.event_ids[0] if statement.event_ids else None)
        return Answer(question=question or statement.question or prompt, answer=statement.answer, supported=True,
                      statement_ids=tuple(s.id for s in support),
                      event_ids=tuple(dict.fromkeys(e for s in support for e in s.event_ids)),
                      entity_ids=tuple(dict.fromkeys(e for s in support for e in s.entity_ids)),
                      reference_tick=statement.reference_tick)

    def follow_up(self, kind):
        if self.last is None:
            return Answer(question=kind, answer="The story does not establish the referent.", supported=False)
        focus = self.last
        # The event being discussed is explicit. Never guess a neighboring event.
        event_id = self.last_event
        return self.ask(kind, focus.focus, event_id=event_id, reference_tick=focus.reference_tick, question=kind)

    def questions(self):
        rows = []
        counts = {}
        for statement in self.document.statements:
            counts[statement.question] = counts.get(statement.question, 0) + 1
        paragraph = 1
        for separator, statement in self.document.layout():
            if separator == "\n\n":
                paragraph += 1
            if not statement.question:
                continue
            question = statement.question
            # Qualify the first occurrence too. Internal event IDs are not
            # visible reading context; paragraph numbers are.
            if statement.paragraph or counts[question] > 1 or "this point" in question:
                question = f"{question} (In paragraph {paragraph}.)"
            row = self.ask(statement.kind, statement.focus,
                           event_id=statement.event_ids[0] if statement.event_ids else None,
                           reference_tick=statement.reference_tick, question=question)
            if row.supported:
                rows.append(row)
        self.last = None
        return rows
