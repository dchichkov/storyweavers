"""
gen6k07.py - Coverage push #07 for gen6.

These kernels were sampled from the highest-frequency missing list with
`sample.py -k ... --show-source` before implementation. They cover common
structural and everyday-story primitives that otherwise fell through as
"Something X happened" or verbed nouns.
"""

from __future__ import annotations

from typing import Any

from gen6 import (
    REGISTRY,
    World,
    Entity,
    Trace,
    NLGUtils,
    to_phrase,
    action_to_phrase,
    base_phrase,
    child_sentences,
    coherent,
    meta_story,
    is_meta_call,
)

from gen6k03 import _split, _phrases, _kw_targets, _cap, _is_char


_FOCUS_KEYS = (
    "actor", "char", "hero", "protagonist", "protagonists", "participants",
    "initiator", "asker", "speaker", "giver", "helper", "teacher", "learner",
    "client", "owner",
)


def _kw_values(kw: dict, *keys: str) -> list[Any]:
    out: list[Any] = []
    for key in keys:
        value = kw.get(key)
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            out.extend(value)
        else:
            out.append(value)
    return out


def _first_char(value: Any) -> Entity | None:
    if _is_char(value):
        return value
    if isinstance(value, (list, tuple)):
        for item in value:
            found = _first_char(item)
            if found is not None:
                return found
    return None


def _actor_from(ctx: World, chars: list[Entity], kw: dict) -> Entity | None:
    if chars:
        return chars[0]
    for key in _FOCUS_KEYS:
        found = _first_char(kw.get(key))
        if found is not None:
            return found
    return ctx.actor


def _sentences(values: list[Any]) -> list[str]:
    out: list[str] = []
    for value in values:
        cs = child_sentences(value)
        if cs is not None:
            out += cs
    return out


def _concepts(values: list[Any]) -> str:
    # A narration Trace is already a sentence; using it as a noun phrase creates
    # artifacts like "the church and the floor". Callers that want those
    # sentences should collect them through `_sentences`.
    phrase_values = [v for v in values if child_sentences(v) is None]
    return NLGUtils.join_list(_phrases(phrase_values))


def _clean_sentence(text: str) -> str:
    """Remove dangling preposition tails left by empty optional targets."""
    fixes = (
        (" with .", "."),
        (" about .", "."),
        (" of .", "."),
        (" for .", "."),
        (" to .", "."),
        (" from .", "."),
        (" by .", "."),
        (" near .", "."),
        (": .", "."),
    )
    for old, new in fixes:
        text = text.replace(old, new)
    return text.replace("  ", " ")


@REGISTRY.kernel("If")
def If(ctx: World, *args: Any, **kw: Any) -> str:
    """Conditional wrapper: If(condition, result) / If(Share(Food), Help(...))."""
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    values = _kw_values(kw, "condition", "when", "then", "result", "outcome") + list(rest)
    sents = _sentences(values)
    phrases = [to_phrase(v) for v in values if child_sentences(v) is None and to_phrase(v)]
    if actor is not None:
        ctx.actor = actor
        if sents:
            lead = f"{ctx.say(actor)} knew what to do."
            return coherent(ctx, actor, [lead] + sents)
        if len(phrases) >= 2:
            return f"{ctx.say(actor)} learned that if {phrases[0]}, then {phrases[1]}."
        if phrases:
            return f"{ctx.say(actor)} thought about whether {phrases[0]}."
    if sents:
        return " ".join(sents)
    if len(phrases) >= 2:
        return f"If {phrases[0]}, then {phrases[1]}."
    return f"If {phrases[0]}." if phrases else "There was a choice to make."


@REGISTRY.kernel("Water")
def Water(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    targets = _phrases(chars[1:]) + _phrases(rest) + _phrases(_kw_targets(kw))
    target = NLGUtils.join_list(targets)
    if actor is not None and target:
        actor.add_meme("Care", 0.2)
        ctx.actor = actor
        return f"{ctx.say(actor)} watered {target}."
    if actor is not None:
        ctx.actor = actor
        return f"{ctx.say(actor)} got some water."
    return f"There was water for {target}." if target else "There was water nearby."


@REGISTRY.kernel("Meal")
def Meal(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    foods = _phrases(chars[1:]) + _phrases(rest) + _phrases(_kw_values(kw, "food", "item", "dish", "meal"))
    food = NLGUtils.join_list(foods)
    if actor is not None:
        actor.add_meme("Joy", 0.2)
        ctx.actor = actor
        return f"{ctx.say(actor)} ate {food} for a meal." if food else f"{ctx.say(actor)} enjoyed a meal."
    return f"Everyone enjoyed a meal of {food}." if food else "Everyone sat down for a meal."


@REGISTRY.kernel("Persistence")
def Persistence(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    if actor is not None and is_meta_call(kw):
        body = meta_story(ctx, actor, kw)
        if body:
            actor.add_meme("Persistence", 1.0)
            return body
    pieces = list(rest) + _kw_values(kw, "desire", "obstacle", "actions", "result", "success")
    sents = _sentences(pieces)
    focus = _concepts([p for p in pieces if child_sentences(p) is None])
    if actor is not None:
        actor.add_meme("Persistence", 1.0)
        actor.add_meme("Determination", 0.5)
        ctx.actor = actor
        lead = f"{ctx.say(actor)} kept trying"
        lead += f" with {focus}." if focus else "."
        return coherent(ctx, actor, [lead] + sents)
    return f"Everyone kept trying with {focus}." if focus else "Everyone kept trying."


@REGISTRY.kernel("ParkVisit")
def ParkVisit(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    if actor is not None and is_meta_call(kw):
        body = meta_story(ctx, actor, kw)
        if body:
            return body
    place = _concepts(rest + _kw_values(kw, "place", "location", "companion"))
    place = place or "the park"
    body = _sentences(rest)
    if actor is not None:
        actor.add_meme("Joy", 0.2)
        ctx.actor = actor
        return coherent(ctx, actor, [f"{ctx.say(actor)} went to {place}."] + body)
    return f"Everyone went to {place}."


@REGISTRY.kernel("Ignore")
def Ignore(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _concepts(chars[1:] + rest + _kw_values(kw, "target", "object", "problem", "warning"))
    if actor is not None:
        actor.add_meme("Indifference", 0.4)
        ctx.actor = actor
        return f"{ctx.say(actor)} ignored {target}." if target else f"{ctx.say(actor)} ignored it."
    return f"Everyone ignored {target}." if target else "It was ignored."


@REGISTRY.kernel("Joyful")
def Joyful(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    if actor is not None and is_meta_call(kw):
        actor.add_meme("Joy", 1.0)
        body = meta_story(ctx, actor, kw)
        if body:
            return body
    target = _concepts(chars[1:] + rest + _kw_targets(kw))
    if actor is not None:
        actor.add_meme("Joy", 1.0)
        ctx.actor = actor
        return f"{ctx.say(actor)} felt joyful about {target}." if target else f"{ctx.say(actor)} felt joyful."
    return f"Everyone felt joyful about {target}." if target else "Everyone felt joyful."


@REGISTRY.kernel("Greeting")
def Greeting(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    speaker = _actor_from(ctx, chars, kw)
    listeners = chars[1:] + rest + _kw_values(kw, "to", "listener", "target")
    words = _concepts(_kw_values(kw, "words", "message"))
    target = _concepts(listeners)
    if speaker is not None:
        speaker.add_meme("Friendliness", 0.3)
        ctx.actor = speaker
        if target and words:
            return f"{ctx.say(speaker)} greeted {target} by saying {words}."
        return f"{ctx.say(speaker)} greeted {target} warmly." if target else f"{ctx.say(speaker)} said hello."
    return f"Everyone greeted {target} warmly." if target else "Everyone said hello."


@REGISTRY.kernel("Competition")
def Competition(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    if actor is not None and is_meta_call(kw):
        actor.add_meme("Competition", 1.0)
        body = meta_story(ctx, actor, kw)
        if body:
            return body
    opponents = _concepts(chars[1:] + rest + _kw_values(kw, "opponent", "opponents", "setting"))
    sents = _sentences(_kw_values(kw, "process", "outcome", "result", "moral"))
    if actor is not None:
        actor.add_meme("Competition", 1.0)
        ctx.actor = actor
        lead = f"{ctx.say(actor)} entered a competition"
        lead += f" with {opponents}." if opponents else "."
        return coherent(ctx, actor, [lead] + sents)
    return f"There was a competition with {opponents}." if opponents else "There was a competition."


@REGISTRY.kernel("Unlock")
def Unlock(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _concepts(chars[1:] + rest + _kw_targets(kw))
    if actor is not None:
        actor.add_meme("Progress", 0.3)
        ctx.actor = actor
        return f"{ctx.say(actor)} unlocked {target}." if target else f"{ctx.say(actor)} unlocked it."
    return f"{_cap(target)} was unlocked." if target else "It was unlocked."


@REGISTRY.kernel("Concern")
def Concern(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _concepts(chars[1:] + rest + _kw_targets(kw))
    if actor is not None:
        actor.add_meme("Concern", 1.0)
        actor.add_meme("Fear", 0.2)
        ctx.actor = actor
        return f"{ctx.say(actor)} was concerned about {target}." if target else f"{ctx.say(actor)} was concerned."
    return f"There was concern about {target}." if target else "Everyone was concerned."


@REGISTRY.kernel("Balance")
def Balance(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    ideas = _concepts(chars[1:] + rest + _kw_values(kw, "between", "with", "and"))
    if actor is not None:
        actor.add_meme("Wisdom", 0.4)
        actor.add_meme("Balance", 1.0)
        ctx.actor = actor
        return f"{ctx.say(actor)} learned to balance {ideas}." if ideas else f"{ctx.say(actor)} learned to find balance."
    return f"It was important to balance {ideas}." if ideas else "It was important to find balance."


@REGISTRY.kernel("Wet")
def Wet(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _concepts(chars[1:] + rest + _kw_targets(kw))
    if actor is not None:
        actor.add_meme("Wet", 1.0)
        ctx.actor = actor
        return f"{ctx.say(actor)} got wet from {target}." if target else f"{ctx.say(actor)} got wet."
    return f"{_cap(target)} was wet." if target else "Everything was wet."


@REGISTRY.kernel("Dry")
def Dry(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _concepts(chars[1:] + rest + _kw_targets(kw))
    if actor is not None and target:
        actor.add_meme("Care", 0.2)
        ctx.actor = actor
        return f"{ctx.say(actor)} dried {target}."
    if actor is not None:
        ctx.actor = actor
        return f"{ctx.say(actor)} got dry again."
    return f"{_cap(target)} dried out." if target else "Everything dried out."


@REGISTRY.kernel("ReturnHome")
def ReturnHome(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actors = chars if chars else ([ctx.actor] if ctx.actor is not None else [])
    place = _concepts(rest + _kw_values(kw, "home", "destination", "to")) or "home"
    if actors:
        for actor in actors:
            actor.add_meme("Relief", 0.2)
        ctx.actor = actors[0]
        who = ctx.say(actors[0]) if len(actors) == 1 else NLGUtils.join_list([str(c) for c in actors])
        return f"{who} went back {place}." if place == "home" else f"{who} returned to {place}."
    return f"Everyone went back {place}." if place == "home" else f"Everyone returned to {place}."


@REGISTRY.kernel("Command")
def Command(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    speaker = _actor_from(ctx, chars, kw)
    listener = chars[1] if len(chars) > 1 else kw.get("to")
    action = kw.get("action") or kw.get("command") or kw.get("request")
    pieces = [action] if action is not None else list(rest)
    action_text = ""
    if pieces:
        action_text = base_phrase(pieces[0]) if isinstance(pieces[0], Trace) else to_phrase(pieces[0])
        if not action_text and isinstance(pieces[0], Trace):
            action_text = action_to_phrase(pieces[0])
    if speaker is not None:
        speaker.add_meme("Authority", 0.4)
        ctx.actor = speaker
        who = f" {to_phrase(listener)}" if listener is not None else ""
        if action_text:
            if not who:
                who = " everyone"
            return f"{ctx.say(speaker)} told{who} to {action_text}."
        return f"{ctx.say(speaker)} gave{who} a command."
    return f"Someone gave a command to {to_phrase(listener)}." if listener is not None else "Someone gave a command."


@REGISTRY.kernel("Agreement")
def Agreement(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    others = _concepts(chars[1:] + rest + _kw_values(kw, "with", "about", "response"))
    if actor is not None:
        actor.add_meme("Agreement", 1.0)
        actor.add_meme("Friendship", 0.2)
        ctx.actor = actor
        return f"{ctx.say(actor)} agreed with {others}." if others else f"{ctx.say(actor)} agreed."
    return f"Everyone agreed about {others}." if others else "Everyone agreed."


@REGISTRY.kernel("Feel")
def Feel(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    feeling = _concepts(chars[1:] + rest + _kw_values(kw, "state", "mood", "feeling"))
    place = _concepts(_kw_values(kw, "in", "at", "with"))
    if actor is not None:
        actor.add_meme("Feeling", 0.5)
        if feeling:
            actor.add_meme(_cap(feeling.split(" ", 1)[0]), 0.4)
        ctx.actor = actor
        tail = f" in {place}" if place else ""
        return f"{ctx.say(actor)} felt {feeling}{tail}." if feeling else f"{ctx.say(actor)} felt something."
    return f"Everyone felt {feeling}." if feeling else "There was a strong feeling."


@REGISTRY.kernel("Dirty")
def Dirty(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _concepts(chars[1:] + rest + _kw_targets(kw))
    if actor is not None:
        actor.add_meme("Dirty", 1.0)
        ctx.actor = actor
        return f"{ctx.say(actor)} got dirty with {target}." if target else f"{ctx.say(actor)} got dirty."
    return f"{_cap(target)} got dirty." if target else "Everything got dirty."


@REGISTRY.kernel("Suggestion")
@REGISTRY.kernel("Suggest")
def Suggestion(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    speaker = _actor_from(ctx, chars, kw)
    target = _concepts(chars[1:] + rest + _kw_targets(kw))
    if speaker is not None:
        speaker.add_meme("Wisdom", 0.2)
        ctx.actor = speaker
        return f"{ctx.say(speaker)} suggested {target}." if target else f"{ctx.say(speaker)} made a suggestion."
    return f"Someone suggested {target}." if target else "Someone made a suggestion."


@REGISTRY.kernel("Steal")
def Steal(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    item = _concepts(chars[1:] + rest + _kw_values(kw, "item", "object", "target"))
    if actor is not None:
        actor.add_meme("Mischief", 0.6)
        actor.add_meme("Theft", 1.0)
        ctx.actor = actor
        return f"{ctx.say(actor)} stole {item}." if item else f"{ctx.say(actor)} stole something."
    return f"Someone stole {item}." if item else "Something was stolen."


@REGISTRY.kernel("Warn")
def Warn(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    speaker = _actor_from(ctx, chars, kw)
    listeners = chars[1:]
    topic = _concepts(rest + _kw_values(kw, "about", "topic", "reason"))
    if speaker is not None:
        speaker.add_meme("Warning", 1.0)
        speaker.add_meme("Authority", 0.2)
        ctx.actor = speaker
        who = f" {NLGUtils.join_list([str(c) for c in listeners])}" if listeners else ""
        tail = f" about {topic}" if topic else ""
        return f"{ctx.say(speaker)} warned{who}{tail}."
    return f"There was a warning about {topic}." if topic else "There was a warning."


@REGISTRY.kernel("Cheer")
def Cheer(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actors = chars if chars else ([ctx.actor] if ctx.actor is not None else [])
    target = _concepts(rest + _kw_values(kw, "for", "target", "observers"))
    if actors:
        for actor in actors:
            actor.add_meme("Joy", 0.3)
        ctx.actor = actors[0]
        who = ctx.say(actors[0]) if len(actors) == 1 else NLGUtils.join_list([str(c) for c in actors])
        return f"{who} cheered for {target}." if target else f"{who} cheered."
    return f"Everyone cheered for {target}." if target else "Everyone cheered."


@REGISTRY.kernel("Win")
def Win(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    prize = _concepts(chars[1:] + rest + _kw_values(kw, "prize", "game", "race"))
    if actor is not None:
        actor.add_meme("Victory", 1.0)
        actor.add_meme("Joy", 0.5)
        actor.add_meme("Pride", 0.3)
        ctx.actor = actor
        return f"{ctx.say(actor)} won {prize}." if prize else f"{ctx.say(actor)} won."
    return f"Someone won {prize}." if prize else "Someone won."


def _register_action(name: str, past: str, *, solo: str = "something", meme: str = "", amount: float = 0.3, prep: str = "") -> None:
    def fn(ctx: World, *args: Any, **kw: Any) -> str:
        chars, rest = _split(args)
        actor = _actor_from(ctx, chars, kw)
        if actor is not None and is_meta_call(kw):
            body = meta_story(ctx, actor, kw)
            if body:
                return body
        target = _concepts(chars[1:] + rest + _kw_targets(kw))
        if actor is not None:
            if meme:
                actor.add_meme(meme, amount)
            ctx.actor = actor
            if name == "Cover" and target in {"eyes", "face", "ears"}:
                return f"{ctx.say(actor)} covered {actor.pronoun('possessive')} {target}."
            tail = f" {prep} {target}" if prep and target else (f" {target}" if target else "")
            return f"{ctx.say(actor)} {past}{tail}." if target else f"{ctx.say(actor)} {past} {solo}."
        return f"Someone {past} {target}." if target else f"{_cap(name)} happened."
    fn.__name__ = name
    REGISTRY.kernel(name)(fn)


def _register_state(name: str, template: str, *, meme: str = "", amount: float = 0.6) -> None:
    def fn(ctx: World, *args: Any, **kw: Any) -> str:
        chars, rest = _split(args)
        actor = _actor_from(ctx, chars, kw)
        target = _concepts(chars[1:] + rest + _kw_targets(kw))
        if actor is not None:
            if meme:
                actor.add_meme(meme, amount)
            ctx.actor = actor
            return _clean_sentence(template.format(s=ctx.say(actor), t=target))
        subject = _cap(target) if target else "Everyone"
        return _clean_sentence(template.format(s=subject, t=""))
    fn.__name__ = name
    REGISTRY.kernel(name)(fn)


def _register_meta(name: str, fallback: str, *, meme: str = "") -> None:
    def fn(ctx: World, *args: Any, **kw: Any) -> str:
        chars, rest = _split(args)
        actor = _actor_from(ctx, chars, kw)
        if actor is not None:
            if meme:
                actor.add_meme(meme, 0.5)
            ctx.actor = actor
            body = meta_story(ctx, actor, kw)
            if body:
                return body
            sents = _sentences(rest)
            if sents:
                return coherent(ctx, actor, [fallback.format(s=ctx.say(actor))] + sents)
            target = _concepts(chars[1:] + rest + _kw_targets(kw))
            return fallback.format(s=ctx.say(actor)) + (f" with {target}." if target else ".")
        sents = _sentences(rest + list(kw.values()))
        if sents:
            return " ".join(sents)
        target = _concepts(rest + _kw_targets(kw))
        return f"{_cap(name)} happened with {target}." if target else f"{_cap(name)} happened."
    fn.__name__ = name
    REGISTRY.kernel(name)(fn)


@REGISTRY.kernel("Clean")
def CleanTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    sents = _sentences(rest + list(kw.values()))
    target = _concepts(chars[1:] + rest + _kw_targets(kw))
    if actor is not None:
        actor.add_meme("Pride", 0.2)
        actor.add_meme("Care", 0.2)
        ctx.actor = actor
        lead = f"{ctx.say(actor)} cleaned {target}." if target else f"{ctx.say(actor)} tidied everything up."
        return coherent(ctx, actor, [lead] + sents)
    if target:
        return f"{_cap(target)} was cleaned."
    return "Everything was cleaned up."


@REGISTRY.kernel("Start")
def Start(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _concepts(chars[1:] + rest + _kw_values(kw, "target", "object", "thing"))
    if target:
        return f"{_cap(target)} started."
    if actor is not None:
        ctx.actor = actor
        actor.add_meme("Initiative", 0.3)
        return f"{ctx.say(actor)} started."
    return "Things started."


@REGISTRY.kernel("Trash")
def Trash(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _concepts(chars[1:] + rest + _kw_values(kw, "on", "in", "at", "target", "object"))
    if actor is not None:
        actor.add_meme("Disgust", 0.3)
        ctx.actor = actor
        return f"{ctx.say(actor)} found trash near {target}." if target else f"{ctx.say(actor)} found trash."
    return f"There was trash near {target}." if target else "There was trash."


@REGISTRY.kernel("Wind")
def Wind(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _concepts(chars[1:] + rest + _kw_values(kw, "around", "through", "target"))
    if actor is not None:
        actor.add_meme("Weather", 0.2)
        ctx.actor = actor
    return f"The wind blew around {target}." if target else "The wind blew."


@REGISTRY.kernel("Wave")
def Wave(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _concepts(chars[1:] + rest + _kw_values(kw, "target", "object"))
    if actor is not None:
        actor.add_meme("Danger", 0.2)
        ctx.actor = actor
    return f"A wave swept over {target}." if target else "A wave swept in."


@REGISTRY.kernel("Proud")
@REGISTRY.kernel("Pride")
def ProudTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _concepts(chars[1:] + rest + _kw_values(kw, "of", "about", "target"))
    if actor is not None:
        actor.add_meme("Pride", 1.0)
        actor.add_meme("Joy", 0.5)
        ctx.actor = actor
        return f"{ctx.say(actor)} felt proud of {target}." if target else f"{ctx.say(actor)} felt proud."
    return f"Everyone felt proud of {target}." if target else "Everyone felt proud."


_register_action("Neglect", "neglected", solo="it", meme="Neglect", amount=0.5)
_register_meta("Playday", "{s} had a playful day", meme="Joy")
_register_action("Smell", "smelled", solo="something", meme="Curiosity", amount=0.1)
_register_state("Dislike", "{s} did not like {t}.", meme="Dislike")
_register_meta("Teaching", "{s} taught a lesson", meme="Wisdom")
_register_action("Meeting", "met", solo="someone", meme="Friendship", amount=0.2)
_register_action("Encouragement", "encouraged", solo="everyone", meme="Kindness", amount=0.3)
_register_action("Decorate", "decorated", solo="everything", meme="Joy", amount=0.2)
_register_state("Awe", "{s} looked on in awe of {t}.", meme="Awe")
_register_state("Separation", "{s} felt separated from {t}.", meme="Sadness", amount=0.3)
_register_action("Fold", "folded", solo="it neatly")
_register_action("Measure", "measured", solo="carefully")
_register_meta("Bath", "{s} took a bath", meme="Clean")
_register_state("Courage", "{s} found courage for {t}.", meme="Brave")
_register_action("PickUp", "picked up", solo="something")
_register_action("Sort", "sorted", solo="everything")
_register_action("Resolve", "resolved", solo="the problem", meme="Wisdom", amount=0.3)
_register_state("Loneliness", "{s} felt lonely.", meme="Sadness")
_register_action("Song", "sang", solo="a song", meme="Joy", amount=0.2)
_register_action("Confrontation", "confronted", solo="the problem", meme="Brave", amount=0.3)
_register_action("Wrap", "wrapped", solo="it up", meme="Care", amount=0.2)
_register_meta("Experiment", "{s} tried an experiment", meme="Curiosity")
_register_state("Skill", "{s} practiced a useful skill with {t}.", meme="Skill")
_register_meta("HideSeek", "{s} played hide and seek", meme="Joy")
_register_action("Nap", "took a nap", solo="", meme="Rest", amount=0.5)
_register_action("Bring", "brought", solo="something")
_register_state("Belief", "{s} believed in {t}.", meme="Hope")
_register_action("Prepare", "prepared", solo="everything")
_register_action("Deliver", "delivered", solo="it")
_register_state("Cold", "{s} felt cold.", meme="Cold")
_register_action("Kiss", "kissed", solo="someone", meme="Love", amount=0.3)
_register_action("View", "looked at", solo="the view", meme="Curiosity", amount=0.1)
_register_action("Transport", "carried", solo="it along")
_register_action("Trick", "tricked", solo="someone", meme="Mischief", amount=0.4)
_register_meta("Ongoing", "{s} kept going", meme="Persistence")
_register_action("Apply", "applied", solo="it carefully")
_register_state("Preference", "{s} preferred {t}.", meme="Preference")
_register_meta("Interaction", "{s} interacted", meme="Friendship")
_register_action("Get", "got", solo="something")
_register_action("Light", "lit", solo="it")
_register_action("Close", "closed", solo="it")
_register_action("Organize", "organized", solo="everything")
_register_state("Miss", "{s} missed {t}.", meme="Sadness", amount=0.3)
_register_action("Slide", "slid on", solo="the slide", meme="Joy", amount=0.2)
_register_state("Imagination", "{s} imagined {t}.", meme="Imagination")
_register_action("Acquire", "acquired", solo="something")
_register_state("Embarrassment", "{s} felt embarrassed.", meme="Embarrassment")
_register_state("Commitment", "{s} made a commitment to {t}.", meme="Commitment")
_register_action("Fight", "fought", solo="bravely", meme="Anger", amount=0.4)
_register_state("Sound", "{s} heard the sound of {t}.", meme="Curiosity", amount=0.1)
_register_state("Disappointment", "{s} felt disappointed about {t}.", meme="Sadness", amount=0.4)
_register_action("Blow", "blew", solo="hard")
_register_state("Condition", "{s} had to deal with {t}.", meme="Condition")
_register_action("Stir", "stirred", solo="everything together")
_register_action("Pour", "poured", solo="carefully")
_register_action("Feast", "feasted on", solo="treats", meme="Joy", amount=0.3)
_register_action("Departure", "left", solo="for a while", meme="Farewell", amount=0.3)
_register_state("Damage", "{s} was damaged.", meme="Damage")
_register_state("Obedience", "{s} listened and obeyed.", meme="Obedience")
_register_state("Mistake", "{s} made a mistake with {t}.", meme="Mistake")
_register_action("Bark", "barked at", solo="something")
_register_action("Hang", "hung", solo="there")
_register_action("Demand", "demanded", solo="an answer")
_register_action("Print", "printed", solo="it")
_register_action("Order", "ordered", solo="something")
_register_action("Appear", "appeared near", solo="everyone")
_register_action("Test", "tested", solo="it")
_register_action("Borrow", "borrowed", solo="something")
_register_action("Snack", "snacked on", solo="something", meme="Joy", amount=0.2)
_register_action("Disobey", "disobeyed", solo="the warning", meme="Disobedience", amount=0.5)
_register_state("Responsibility", "{s} learned responsibility.", meme="Responsibility")
_register_action("Spray", "sprayed", solo="water")
_register_action("Prompt", "prompted", solo="a response")
_register_action("Load", "loaded", solo="everything")
_register_meta("Performance", "{s} gave a performance", meme="Joy")
_register_action("Confront", "confronted", solo="the problem", meme="Brave", amount=0.3)
_register_action("Cover", "covered", solo="it")
_register_action("Arrive", "arrived at", solo="the place", meme="Joy", amount=0.1)
_register_action("Sail", "sailed", solo="away", meme="Joy", amount=0.2)
_register_state("Rejection", "{s} felt rejected by {t}.", meme="Sadness", amount=0.4)
_register_action("Alert", "alerted", solo="everyone", meme="Concern", amount=0.4)
_register_state("No", "{s} said no to {t}.", meme="Refusal", amount=0.4)
_register_action("Instruction", "gave instructions about", solo="what to do", meme="Wisdom", amount=0.2)
_register_state("Possession", "{s} had {t}.", meme="Possession", amount=0.3)
_register_action("Burn", "burned", solo="badly", meme="Danger", amount=0.3)
_register_action("Forgive", "forgave", solo="them", meme="Forgiveness", amount=0.5)
_register_state("Struggle", "{s} struggled with {t}.", meme="Struggle", amount=0.5)
_register_action("Wake", "woke up", solo="", meme="Awake", amount=0.3)
_register_meta("Daily", "{s} did it every day", meme="Routine")
_register_action("Bandage", "bandaged", solo="the hurt place", meme="Care", amount=0.3)
_register_state("Warmth", "{s} felt warmth from {t}.", meme="Love", amount=0.3)
_register_state("Reconciliation", "{s} made peace with {t}.", meme="Forgiveness", amount=0.5)
_register_meta("Stay", "{s} stayed", meme="Patience")
_register_action("Replace", "replaced", solo="it")
_register_state("Mystery", "{s} found a mystery in {t}.", meme="Curiosity", amount=0.4)
_register_state("Heat", "{s} felt heat from {t}.", meme="Heat")
_register_state("Rule", "{s} followed a rule about {t}.", meme="Obedience", amount=0.3)
_register_action("Trade", "traded", solo="something")
_register_action("Speak", "said", solo="something")
_register_state("Solution", "{s} found a solution with {t}.", meme="Wisdom", amount=0.4)
_register_meta("StoreVisit", "{s} went to the store", meme="Need")
_register_action("Lick", "licked", solo="gently", meme="Love", amount=0.2)
_register_state("Crying", "{s} was crying.", meme="Sadness", amount=0.7)
_register_meta("Preparation", "{s} got ready", meme="Preparation")
_register_state("Night", "{s} spent the night with {t}.", meme="Rest", amount=0.3)
_register_state("Affection", "{s} showed affection for {t}.", meme="Love", amount=0.6)
_register_state("Frustration", "{s} felt frustrated with {t}.", meme="Anger", amount=0.3)
_register_state("Disgust", "{s} felt disgusted by {t}.", meme="Disgust", amount=0.5)
_register_action("Nurture", "nurtured", solo="it", meme="Care", amount=0.4)
_register_state("Treasure", "{s} found treasure: {t}.", meme="Joy", amount=0.3)
_register_action("Spit", "spat out", solo="something")
_register_meta("Race", "{s} joined a race", meme="Competition")
_register_action("Lead", "led", solo="the way", meme="Leadership", amount=0.3)
_register_meta("Heroic", "{s} did something heroic", meme="Brave")
_register_action("Scatter", "scattered", solo="everywhere")
_register_state("Worry", "{s} worried about {t}.", meme="Fear", amount=0.3)
_register_meta("Resist", "{s} resisted", meme="Willpower")
_register_state("Feeling", "{s} felt {t}.", meme="Feeling")
_register_action("Story", "told a story about", solo="something", meme="Story", amount=0.3)
_register_state("Tired", "{s} felt tired.", meme="Fatigue")
_register_state("Secret", "{s} kept a secret about {t}.", meme="Secret")
_register_action("Descend", "climbed down from", solo="there")
_register_state("Together", "{s} stayed together with {t}.", meme="Friendship", amount=0.3)
_register_action("Heed", "listened to", solo="the warning", meme="Wisdom", amount=0.3)
_register_action("Display", "displayed", solo="it proudly", meme="Pride", amount=0.2)
_register_state("Mastery", "{s} mastered {t}.", meme="Skill", amount=0.6)
_register_action("Wander", "wandered through", solo="around")
_register_state("Fatigue", "{s} felt tired.", meme="Fatigue")
_register_state("Patience", "{s} showed patience with {t}.", meme="Patience")
_register_meta("Day", "{s} had a busy day", meme="Joy")
_register_action("Sell", "sold", solo="something")
_register_state("Ready", "{s} got ready for {t}.", meme="Readiness")
_register_meta("JoyfulPlay", "{s} played joyfully", meme="Joy")
_register_state("Delay", "{s} was delayed by {t}.", meme="Patience", amount=0.2)
_register_action("Reprimand", "reprimanded", solo="someone", meme="Authority", amount=0.3)
_register_action("Spread", "spread", solo="out")
_register_action("Record", "recorded", solo="it")
_register_state("Freedom", "{s} felt free from {t}.", meme="Freedom")
_register_meta("Playful", "{s} played happily", meme="Joy")
_register_action("Admire", "admired", solo="it", meme="Awe", amount=0.2)
_register_meta("Redemption", "{s} found redemption", meme="Wisdom")
_register_action("Allow", "allowed", solo="it")
_register_action("Scold", "scolded", solo="someone", meme="Authority", amount=0.3)
_register_state("Jealousy", "{s} felt jealous of {t}.", meme="Envy", amount=0.5)
_register_meta("Negotiation", "{s} negotiated", meme="Agreement")
_register_action("Shrink", "shrank", solo="down")
_register_action("TurnTaking", "took turns with", solo="everyone", meme="Friendship", amount=0.3)
_register_state("Achievement", "{s} achieved {t}.", meme="Pride", amount=0.5)
_register_action("Crash", "crashed into", solo="something", meme="Surprise", amount=0.3)
_register_action("Greet", "greeted", solo="everyone", meme="Friendliness", amount=0.3)
_register_action("Attach", "attached", solo="it")
_register_state("Confusion", "{s} felt confused by {t}.", meme="Confusion")
_register_state("Discomfort", "{s} felt uncomfortable with {t}.", meme="Discomfort")
_register_action("Rush", "rushed toward", solo="ahead")
_register_meta("School", "{s} went to school", meme="Learning")
_register_state("Politeness", "{s} was polite about {t}.", meme="Kindness", amount=0.2)
_register_action("Exercise", "exercised", solo="hard", meme="Health", amount=0.2)
_register_meta("SearchParty", "{s} joined a search party", meme="Search")
_register_action("Guard", "guarded", solo="it", meme="Protection", amount=0.3)
_register_action("Shine", "shone on", solo="brightly", meme="Joy", amount=0.1)
_register_action("Finish", "finished", solo="it", meme="Completion", amount=0.4)
_register_action("Wag", "wagged", solo="happily", meme="Joy", amount=0.2)
_register_action("AskHelp", "asked for help from", solo="someone", meme="Wisdom", amount=0.3)
_register_state("Completion", "{s} finished {t}.", meme="Completion")
_register_action("Treat", "treated", solo="kindly", meme="Kindness", amount=0.3)
_register_state("Angry", "{s} felt angry about {t}.", meme="Anger", amount=0.7)
_register_action("Polish", "polished", solo="it")
_register_action("Bury", "buried", solo="it")
_register_meta("Transition", "{s} went through a change", meme="Change")
_register_state("Shelter", "{s} found shelter in {t}.", meme="Safety", amount=0.4)
_register_state("Distraction", "{s} was distracted by {t}.", meme="Distraction")
_register_state("Empty", "{s} was empty.", meme="Emptiness")
_register_action("SeekHelp", "looked for help from", solo="someone", meme="Wisdom", amount=0.3)
_register_action("Shout", "shouted at", solo="someone", meme="Anger", amount=0.2)
_register_state("Peaceful", "{s} felt peaceful.", meme="Peace", amount=0.5)
_register_action("Report", "reported", solo="what happened")
_register_action("Study", "studied", solo="carefully", meme="Wisdom", amount=0.3)
_register_state("Effort", "{s} made an effort with {t}.", meme="Persistence", amount=0.4)
_register_state("Approval", "{s} showed approval.", meme="Approval", amount=0.4)
_register_action("Collapse", "collapsed near", solo="there", meme="Surprise", amount=0.2)
_register_state("Heavy", "{s} was heavy.", meme="Weight")
_register_action("Restore", "restored", solo="it", meme="Repair", amount=0.4)
_register_action("Compliment", "complimented", solo="someone", meme="Kindness", amount=0.3)
_register_action("Melt", "melted", solo="away")
_register_meta("Event", "{s} experienced an event", meme="Surprise")
_register_state("Hospital", "{s} went to the hospital.", meme="Healing")
_register_action("Wipe", "wiped", solo="it clean")
_register_state("Tool", "{s} used a tool: {t}.", meme="Tool")
_register_meta("Proposal", "{s} made a proposal", meme="Idea")
_register_state("End", "{s} came to an end with {t}.", meme="Ending")
_register_action("Cross", "crossed", solo="carefully")
_register_state("Beauty", "{s} saw beauty in {t}.", meme="Awe", amount=0.3)
_register_action("Obtain", "obtained", solo="something")
_register_action("Provide", "provided", solo="what was needed", meme="Kindness", amount=0.3)
_register_state("Fail", "{s} failed at {t}.", meme="Failure", amount=0.5)
_register_state("Generosity", "{s} showed generosity with {t}.", meme="Kindness", amount=0.6)
_register_action("Unpack", "unpacked", solo="everything")
_register_action("Transfer", "transferred", solo="it")
_register_state("Punishment", "{s} faced a punishment from {t}.", meme="Sadness", amount=0.3)
_register_action("Split", "split", solo="it")
_register_action("PutOn", "put on", solo="something")
_register_action("Notice", "noticed", solo="something", meme="Curiosity", amount=0.2)
_register_action("Press", "pressed", solo="it")
_register_state("Reputation", "{s} had a reputation for {t}.", meme="Reputation")
_register_action("Send", "sent", solo="it")
_register_state("Delight", "{s} felt delighted by {t}.", meme="Joy", amount=0.5)
_register_state("Lack", "{s} lacked {t}.", meme="Need", amount=0.3)
_register_meta("SharedPlay", "{s} played together", meme="Friendship")
_register_state("Assistance", "{s} received assistance with {t}.", meme="Help", amount=0.4)
_register_action("Tear", "tore", solo="it")
_register_state("Prayer", "{s} made a prayer for {t}.", meme="Hope", amount=0.4)
_register_action("Design", "designed", solo="something")
_register_state("Validation", "{s} felt validated by {t}.", meme="Confidence", amount=0.4)
_register_meta("Aspiration", "{s} followed an aspiration", meme="Desire")
_register_action("Pocket", "put away", solo="in a pocket")
_register_action("Pass", "passed", solo="it along")
_register_state("Full", "{s} was full.", meme="Fullness")
_register_action("Trap", "trapped", solo="someone", meme="Danger", amount=0.3)
_register_meta("JoyfulDay", "{s} had a joyful day", meme="Joy")
_register_action("Examine", "examined", solo="it", meme="Curiosity", amount=0.3)
_register_action("Cleanup", "cleaned up", solo="the mess", meme="Care", amount=0.3)
_register_action("CleanUp", "cleaned up", solo="the mess", meme="Care", amount=0.3)
_register_action("PutAway", "put away", solo="the thing")
_register_state("Unity", "{s} stood together with {t}.", meme="Friendship", amount=0.5)
_register_action("Extinguish", "put out", solo="the fire", meme="Safety", amount=0.4)
_register_meta("HappyEverAfter", "{s} lived happily ever after", meme="Joy")
_register_state("Absence", "{s} was missing {t}.", meme="Sadness", amount=0.3)
_register_state("Scared", "{s} was scared of {t}.", meme="Fear", amount=0.7)
_register_action("Tease", "teased", solo="someone", meme="Mischief", amount=0.3)
_register_action("Attack", "attacked", solo="suddenly", meme="Danger", amount=0.6)
_register_meta("Delivery", "{s} made a delivery", meme="Responsibility")
_register_meta("Dinner", "{s} had dinner", meme="Food")
_register_action("Obey", "obeyed", solo="the rule", meme="Obedience", amount=0.5)
_register_state("BestFriends", "{s} became best friends with {t}.", meme="Friendship", amount=1.0)
_register_state("Reluctance", "{s} felt reluctant about {t}.", meme="Hesitation", amount=0.4)
_register_state("Recognition", "{s} recognized {t}.", meme="Awareness", amount=0.4)
_register_state("Shiny", "{s} was shiny.", meme="Beauty", amount=0.2)
_register_state("Content", "{s} felt content with {t}.", meme="Joy", amount=0.4)
_register_action("Stand", "stood by", solo="there")
_register_meta("Birthday", "{s} had a birthday", meme="Joy")
_register_action("Step", "stepped on", solo="carefully")
_register_action("Exit", "left", solo="the place")
_register_action("RequestHelp", "asked help from", solo="someone", meme="Wisdom", amount=0.3)
_register_meta("Pursuit", "{s} gave chase", meme="Search")
_register_meta("PlayOutside", "{s} played outside", meme="Joy")
_register_action("Shoot", "shot toward", solo="the target")
_register_state("Constraint", "{s} faced a constraint about {t}.", meme="Constraint")
_register_meta("Incident", "{s} had an incident", meme="Surprise")
_register_state("Restriction", "{s} faced a restriction about {t}.", meme="Restriction")
_register_action("Pause", "paused near", solo="there", meme="Patience", amount=0.2)
_register_action("Pinch", "pinched", solo="a little")
_register_state("Special", "{s} was special because of {t}.", meme="Importance", amount=0.4)
_register_state("Sick", "{s} felt sick.", meme="Sickness", amount=0.7)
_register_meta("Park", "{s} went to the park", meme="Joy")
_register_action("Dive", "dived into", solo="it")
_register_action("OfferHelp", "offered help to", solo="someone", meme="Kindness", amount=0.4)
_register_state("Found", "{s} found {t}.", meme="Discovery", amount=0.5)
_register_action("Roar", "roared at", solo="loudly", meme="Power", amount=0.3)
_register_action("Bump", "bumped into", solo="something", meme="Surprise", amount=0.2)
_register_action("Prohibit", "forbade", solo="it", meme="Authority", amount=0.4)
_register_state("Silence", "{s} was silent about {t}.", meme="Quiet", amount=0.3)
_register_meta("Interruption", "{s} was interrupted", meme="Surprise")
_register_meta("Argument", "{s} argued", meme="Conflict")
_register_meta("Cycle", "{s} went through a cycle", meme="Routine")
_register_action("Plea", "pleaded with", solo="someone", meme="Need", amount=0.4)
_register_state("Speed", "{s} moved with speed around {t}.", meme="Energy", amount=0.3)
_register_meta("Conversation", "{s} had a conversation", meme="Communication")
_register_state("Food", "{s} had food: {t}.", meme="Food", amount=0.3)
_register_state("Expectation", "{s} expected {t}.", meme="Expectation", amount=0.3)
_register_state("Boredom", "{s} felt bored with {t}.", meme="Boredom", amount=0.6)
_register_meta("FunDay", "{s} had a fun day", meme="Joy")
_register_state("Inclusion", "{s} was included with {t}.", meme="Friendship", amount=0.4)
_register_meta("Adaptation", "{s} adapted", meme="Flexibility")
_register_action("Craft", "crafted", solo="something", meme="Creativity", amount=0.3)
_register_action("Ascend", "climbed up toward", solo="higher")
_register_state("Never", "{s} never wanted {t}.", meme="Refusal", amount=0.3)
_register_state("Identity", "{s} knew an identity: {t}.", meme="Identity", amount=0.4)
_register_meta("Teamwork", "{s} worked as a team", meme="Friendship")
_register_state("Vigilance", "{s} stayed watchful for {t}.", meme="Awareness", amount=0.4)
_register_action("Exchange", "exchanged", solo="something")
_register_meta("Quarrel", "{s} quarreled", meme="Conflict")
_register_state("Lose", "{s} lost {t}.", meme="Loss", amount=0.5)
_register_state("Compliance", "{s} complied with {t}.", meme="Obedience", amount=0.5)
_register_meta("Inspiration", "{s} found inspiration", meme="Inspiration")
_register_meta("SimpleJoy", "{s} felt simple joy", meme="Joy")
_register_state("Cool", "{s} was cool.", meme="Cool")
_register_state("Locked", "{s} was locked.", meme="Constraint")
_register_action("Squeeze", "squeezed", solo="gently")
_register_meta("Ritual", "{s} followed a ritual", meme="Routine")
_register_meta("Compromise", "{s} found a compromise", meme="Agreement")
_register_state("Height", "{s} noticed the height of {t}.", meme="Awareness", amount=0.2)
_register_meta("Investigation", "{s} investigated", meme="Curiosity")
_register_meta("Morning", "{s} began the morning", meme="Routine")
_register_action("Gaze", "gazed at", solo="something", meme="Awe", amount=0.2)
_register_state("Free", "{s} was free from {t}.", meme="Freedom", amount=0.5)
_register_state("Anxiety", "{s} felt anxious about {t}.", meme="Fear", amount=0.5)
_register_state("Picture", "{s} saw a picture of {t}.", meme="Awareness", amount=0.2)
_register_action("Pay", "paid", solo="for it")
_register_state("Messy", "{s} was messy.", meme="Mess", amount=0.5)
_register_action("Destroy", "destroyed", solo="it", meme="Damage", amount=0.6)
_register_action("Slap", "slapped", solo="suddenly", meme="Conflict", amount=0.5)
_register_meta("Reading", "{s} read", meme="Learning")
_register_action("Pop", "popped", solo="suddenly", meme="Surprise", amount=0.3)
_register_state("Awareness", "{s} became aware of {t}.", meme="Awareness", amount=0.5)
_register_state("Overcome", "{s} overcame {t}.", meme="Brave", amount=0.5)
_register_meta("Helping", "{s} helped", meme="Kindness")
_register_meta("Storytelling", "{s} told a story", meme="Story")
_register_meta("Resilience", "{s} showed resilience", meme="Persistence")
_register_action("FlyAway", "flew away from", solo="there")
_register_action("Separate", "separated", solo="apart")
_register_state("Connection", "{s} felt connected with {t}.", meme="Friendship", amount=0.4)
_register_action("RunAway", "ran away from", solo="there", meme="Fear", amount=0.3)
_register_state("Message", "{s} received a message about {t}.", meme="Communication", amount=0.3)
_register_action("Overeat", "ate too much of", solo="food")
_register_action("Scream", "screamed at", solo="the surprise", meme="Fear", amount=0.3)
_register_meta("Baking", "{s} baked", meme="Food")
_register_state("Protection", "{s} protected {t}.", meme="Protection", amount=0.5)
_register_state("Future", "{s} looked toward the future of {t}.", meme="Hope", amount=0.3)
_register_state("Deception", "{s} hid the truth about {t}.", meme="Deception", amount=0.5)
_register_state("Resistance", "{s} resisted {t}.", meme="Willpower", amount=0.5)
_register_action("Assemble", "assembled", solo="it")
_register_state("Shame", "{s} felt ashamed about {t}.", meme="Shame", amount=0.5)
_register_meta("Breakfast", "{s} had breakfast", meme="Food")
_register_state("Panic", "{s} panicked about {t}.", meme="Fear", amount=0.7)
_register_meta("Bedtime", "{s} went to bed", meme="Rest")
_register_action("Name", "named", solo="it")
_register_action("Prevent", "prevented", solo="trouble", meme="Protection", amount=0.4)
_register_action("Yell", "yelled at", solo="someone", meme="Anger", amount=0.3)
_register_meta("Announcement", "{s} made an announcement", meme="Communication")
_register_action("Sneak", "snuck toward", solo="there", meme="Mischief", amount=0.3)
_register_state("Nest", "{s} had a nest with {t}.", meme="Home", amount=0.3)
_register_state("Injured", "{s} was injured by {t}.", meme="Pain", amount=0.7)
_register_action("Jog", "jogged with", solo="energy", meme="Health", amount=0.2)
_register_action("Crawl", "crawled through", solo="along")
_register_state("Remorse", "{s} felt remorse about {t}.", meme="Regret", amount=0.6)
_register_state("Favorite", "{s} had a favorite: {t}.", meme="Preference", amount=0.3)
_register_action("Retreat", "retreated to", solo="safety", meme="Fear", amount=0.3)
_register_state("Ignorance", "{s} did not know about {t}.", meme="Ignorance", amount=0.4)
_register_meta("Transaction", "{s} made a transaction", meme="Exchange")
_register_state("Thirst", "{s} was thirsty.", meme="Need", amount=0.5)
_register_state("Intent", "{s} intended {t}.", meme="Desire", amount=0.4)
_register_action("Imagine", "imagined", solo="something", meme="Creativity", amount=0.3)
_register_state("Distress", "{s} felt distress about {t}.", meme="Sadness", amount=0.5)
_register_state("Isolation", "{s} felt isolated from {t}.", meme="Loneliness", amount=0.5)
_register_state("Why", "{s} wondered why {t}.", meme="Curiosity", amount=0.3)
_register_action("Rebuild", "rebuilt", solo="it", meme="Persistence", amount=0.3)
_register_meta("Setup", "{s} set things up", meme="Preparation")
_register_meta("Outing", "{s} went on an outing", meme="Joy")
_register_state("Color", "{s} noticed the color of {t}.", meme="Awareness", amount=0.2)
_register_state("Humor", "{s} found humor in {t}.", meme="Joy", amount=0.3)
_register_meta("Cooking", "{s} cooked", meme="Food")
_register_state("Disappearance", "{s} disappeared from {t}.", meme="Loss", amount=0.4)
_register_state("Alone", "{s} was alone with {t}.", meme="Loneliness", amount=0.4)
_register_meta("Reconcile", "{s} reconciled", meme="Forgiveness")
_register_action("Block", "blocked", solo="the way", meme="Obstacle", amount=0.4)
_register_meta("Trial", "{s} tried something", meme="Learning")
_register_state("Diagnosis", "{s} diagnosed {t}.", meme="Healing", amount=0.4)
_register_state("Disaster", "{s} faced disaster with {t}.", meme="Danger", amount=0.6)
_register_state("Importance", "{s} understood the importance of {t}.", meme="Wisdom", amount=0.4)
_register_meta("Service", "{s} served", meme="Duty")
_register_state("Learned", "{s} learned {t}.", meme="Wisdom", amount=0.5)
_register_state("Prohibition", "{s} was prohibited from {t}.", meme="Restriction", amount=0.4)
_register_state("Empowered", "{s} felt empowered by {t}.", meme="Confidence", amount=0.5)
_register_meta("Mentorship", "{s} received mentorship", meme="Learning")
_register_action("Deny", "denied", solo="it", meme="Refusal", amount=0.4)
_register_meta("Persuasion", "{s} tried persuasion", meme="Communication")
_register_action("Say", "said", solo="something", meme="Communication", amount=0.2)
_register_state("Near", "{s} was near {t}.", meme="Proximity", amount=0.2)
_register_state("Treatment", "{s} received treatment for {t}.", meme="Healing", amount=0.5)
_register_state("Sorry", "{s} felt sorry about {t}.", meme="Regret", amount=0.5)
_register_action("Mock", "mocked", solo="someone", meme="Cruelty", amount=0.4)
_register_meta("Perform", "{s} performed", meme="Performance")
_register_action("Ruin", "ruined", solo="it", meme="Damage", amount=0.5)
_register_state("Reciprocity", "{s} returned kindness to {t}.", meme="Kindness", amount=0.5)
_register_state("Health", "{s} cared about health with {t}.", meme="Health", amount=0.4)
_register_action("Locate", "located", solo="it", meme="Discovery", amount=0.3)
_register_state("Amazement", "{s} was amazed by {t}.", meme="Awe", amount=0.5)
_register_state("Motivation", "{s} felt motivated by {t}.", meme="Desire", amount=0.4)
_register_action("Reply", "replied to", solo="someone", meme="Communication", amount=0.2)
_register_action("BandAid", "put a bandage on", solo="the hurt place", meme="Healing", amount=0.3)
_register_action("Float", "floated with", solo="it")
_register_state("Gain", "{s} gained {t}.", meme="Gain", amount=0.4)
_register_state("Location", "{s} was at {t}.", meme="Place", amount=0.2)
_register_action("Cuddle", "cuddled", solo="close", meme="Love", amount=0.4)
_register_action("Crack", "cracked", solo="open", meme="Surprise", amount=0.2)
_register_meta("DressUp", "{s} dressed up", meme="Play")
_register_meta("Evening", "{s} spent the evening", meme="Routine")
_register_action("Reverse", "reversed", solo="it")
_register_action("Insult", "insulted", solo="someone", meme="Cruelty", amount=0.4)
_register_action("TurnOn", "turned on", solo="something")
_register_action("Apologize", "apologized to", solo="someone", meme="Regret", amount=0.4)
_register_meta("Mediation", "{s} mediated", meme="Agreement")
_register_state("NoFear", "{s} was not afraid of {t}.", meme="Brave", amount=0.5)
_register_action("Animate", "animated", solo="the scene")
_register_state("Note", "{s} noticed a note about {t}.", meme="Communication", amount=0.2)
_register_action("Snuggle", "snuggled with", solo="something warm", meme="Love", amount=0.4)
_register_state("Consent", "{s} consented to {t}.", meme="Agreement", amount=0.5)
_register_action("Introduce", "introduced", solo="someone", meme="Communication", amount=0.3)
_register_meta("ContinuePlay", "{s} kept playing", meme="Joy")
_register_action("Photo", "took a photo of", solo="it")
_register_action("Sip", "sipped", solo="water")
_register_action("Shift", "shifted from", solo="one thing to another", meme="Change", amount=0.3)
_register_meta("Adventures", "{s} had adventures", meme="Adventure")
_register_action("Consume", "consumed", solo="food")
_register_meta("Harvest", "{s} harvested", meme="Food")
_register_action("Soak", "soaked", solo="it")
_register_meta("StoreTrip", "{s} went to the store", meme="Need")
_register_action("Weigh", "weighed", solo="it")
_register_meta("PlayAgain", "{s} played again", meme="Joy")
_register_state("Spoiled", "{s} was spoiled.", meme="Decay", amount=0.4)
_register_action("Surrender", "surrendered", solo="it", meme="Acceptance", amount=0.4)
_register_meta("Retrieval", "{s} retrieved something", meme="Search")
_register_action("Raise", "raised", solo="it")
_register_state("Adopt", "{s} adopted {t}.", meme="Care", amount=0.4)
_register_state("Gentle", "{s} was gentle with {t}.", meme="Kindness", amount=0.4)
_register_action("Welcome", "welcomed", solo="everyone", meme="Kindness", amount=0.3)
_register_action("Guess", "guessed", solo="the answer", meme="Curiosity", amount=0.2)
_register_meta("Revelation", "{s} had a revelation", meme="Discovery")
_register_state("Misunderstanding", "{s} misunderstood {t}.", meme="Confusion", amount=0.5)


if __name__ == "__main__":
    import gen6registry  # noqa: F401
    from gen6 import generate

    tests = [
        "Tim(Character, boy)\nLily(Character, girl)\nGreeting(Tim, Lily)",
        "Lily(Character, girl)\nMeal(sandwich) + Joyful",
        "Max(Character, dog)\nPersistence(Max, actions=Attempt(handle) + Success(water))",
        "Lily(Character, girl)\nParkVisit(Lily, place=park)",
        "Lily(Character, girl)\nIf(Share(Food), Help(Pain) + Relief)",
    ]
    for i, test in enumerate(tests, 1):
        print(f"--- TEST {i} ---")
        print(generate(test))
        print()
