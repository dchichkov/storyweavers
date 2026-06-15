"""Core renderer pack for high-frequency gen7 frame kinds."""

from gen7 import (
    REGISTRY,
    cap,
    display_type,
    emotion_word,
    is_character,
    is_plural,
    join,
    phrase,
)


SCENE_PLAY_PLACES = {"beach", "sand", "park", "garden", "yard", "grass", "woods", "playground"}


def place_prep(place):
    if place in {"beach", "sand"}:
        return "on"
    if place in {"park", "playground"}:
        return "at"
    return "in"


def action_goal_from_object(renderer, obj):
    action = display_type(obj)
    if action == "jump":
        if obj.traits:
            target = renderer.world.object_phrase(renderer.world.physical(obj.traits[0]))
            return f"jump into {target}"
        return "jump"
    if action == "play":
        if obj.traits:
            target = renderer.world.object_phrase(renderer.world.physical(obj.traits[0]))
            return f"play with {target}"
        return "play"
    return ""


def plain_object_phrase(renderer, obj):
    return renderer.world.object_phrase(obj, status=[], owner_id=None, snapshot_owner=True)


@REGISTRY.renderer("want")
def render_want(renderer, frame):
    subject = renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    concepts = renderer.concepts(frame)
    if frame.goal is not None and getattr(frame.goal, "kind", None) == "character":
        return f"{subject} wanted help from {renderer.obj(frame.goal)}."
    if frame.meta.get("desired_action") == "help":
        return f"{subject} wanted to help with {objects or 'it'}."
    if any(display_type(o) == "grow" for o in frame.objects) or "grow" in concepts:
        return f"{subject} wanted to grow."
    if any(display_type(o) == "play" for o in frame.objects) or "play" in concepts:
        return f"{subject} wanted to play."
    if any(display_type(o) == "return" for o in frame.objects) or "return" in concepts:
        return f"{subject} wanted to go back."
    if len(frame.objects) == 1:
        action_goal = action_goal_from_object(renderer, frame.objects[0])
        if action_goal:
            return f"{subject} wanted to {action_goal}."
    goal = phrase(frame.goal, renderer.world) or objects or (concepts[0] if concepts else "something special")
    if goal == "grow":
        return f"{subject} wanted to grow."
    if frame.goal is not None and type(frame.goal).__name__ == "LowerExpr" and frame.goal.name in {"find", "search", "rescue", "fix", "return", "retrieve"}:
        return f"{subject} wanted to {goal}."
    return f"{subject} wanted {goal}."


@REGISTRY.renderer("find", "discover")
def render_find(renderer, frame):
    subject = renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    if frame.patient:
        return f"{subject} found {renderer.obj(frame.patient)}."
    regular, positioned = renderer.split_position_objects(frame.objects)
    if positioned and regular:
        found = join([renderer.obj(o) for o in regular])
        where = join([renderer.obj(o) for o in positioned])
        return f"{subject} found {found} {where}."
    object_names = [display_type(o) for o in frame.objects]
    if "hook" in object_names and "cheap" in object_names:
        return f"{subject} found a simple hook."
    return f"{subject} found {objects}." if objects else f"{subject} found something new."


@REGISTRY.renderer("lost", "lose")
def render_lost(renderer, frame):
    subject = renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    where = ""
    if frame.location is not None:
        loc = display_type(frame.location)
        if loc == "bottom" and frame.location.traits:
            where = f" at the bottom of {renderer.world.object_phrase(renderer.world.physical(frame.location.traits[0]))}"
        else:
            where = f" near {renderer.obj(frame.location)}"
    if objects and frame.actor:
        return f"{subject} lost {objects}{where} and felt sad."
    if frame.patient:
        return f"{subject} lost {renderer.obj(frame.patient)} and felt sad."
    return f"{cap(objects)} was lost{where}." if objects else ""


@REGISTRY.renderer("search")
def render_search(renderer, frame):
    subject = renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    if frame.source.lower() == "investigation":
        return f"{subject} investigated."
    if len(frame.objects) == 1 and display_type(frame.objects[0]) == "under" and frame.objects[0].traits:
        return f"{subject} looked under {renderer.world.object_phrase(renderer.world.physical(frame.objects[0].traits[0]))}."
    if len(frame.objects) == 1 and display_type(frame.objects[0]) in {"pond", "park", "woods"}:
        return f"{subject} searched around {renderer.obj(frame.objects[0])}."
    return f"{subject} looked everywhere for {objects}." if objects else f"{subject} searched carefully."


@REGISTRY.renderer("ask")
def render_ask(renderer, frame):
    subject = renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    target = renderer.obj(frame.patient) if frame.patient else ""
    action_goal = renderer.action_goal(frame.goal)
    if frame.goal is not None and getattr(frame.goal, "kind", None) == "physical":
        thing = objects or plain_object_phrase(renderer, frame.goal)
    else:
        thing = objects or phrase(frame.goal, renderer.world)
    if target and thing:
        if action_goal:
            return f"{subject} asked {target} to {action_goal}."
        if frame.goal is not None and type(frame.goal).__name__ == "LowerExpr" and frame.goal.name in {"find", "retrieve"}:
            return f"{subject} asked {target} to {thing}."
        preposition = "about" if frame.source.lower() == "dialogue" else "for"
        return f"{subject} asked {target} {preposition} {thing}."
    if target:
        return f"{subject} asked {target} for help."
    return f"{subject} asked for help."


@REGISTRY.renderer("help", "rescue")
def render_help(renderer, frame):
    subject = renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    assisted = frame.meta.get("assisted_action")
    if frame.kind == "help" and assisted:
        if assisted == "ask":
            return f"{subject} helped by asking for help."
        action = "take off" if assisted == "remove" else assisted
        return f"{subject} helped {action} {objects or renderer.obj(frame.patient)}."
    if frame.kind == "help" and len(frame.objects) == 1 and display_type(frame.objects[0]) in {"remove", "push", "clean", "wrap", "store", "take care", "carry", "pull"}:
        return f"{subject} helped {renderer.action_object(frame.objects[0])}."
    target = renderer.obj(frame.patient) if frame.patient else (objects or "someone")
    verb = "rescued" if frame.kind == "rescue" else "helped"
    if frame.kind == "rescue" and frame.actor is not None and frame.actor.pronoun("subject") == "it":
        return f"{frame.actor.id} rescued {target}."
    if frame.source.lower() == "kindness" and frame.patient is None and not objects:
        name = frame.actor.id if frame.actor is not None else subject
        copula = "were" if frame.actor is not None and is_plural(display_type(frame.actor)) else "was"
        return f"{name} {copula} kind."
    if frame.patient is None and not objects and frame.kind == "help":
        return f"{subject} helped."
    return f"{subject} {verb} {target}."


@REGISTRY.renderer("play")
def render_play(renderer, frame):
    subject = renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    party = renderer.participants(frame)
    if party and len(frame.meta.get("participants", [])) > 1:
        if len(frame.objects) == 1 and display_type(frame.objects[0]) in SCENE_PLAY_PLACES:
            place = display_type(frame.objects[0])
            prep = place_prep(place)
            return f"{party} played {prep} {renderer.obj(frame.objects[0])}."
        return f"{party} played with {objects}." if objects else f"{party} played together."
    if frame.patient:
        return f"{subject} played with {renderer.obj(frame.patient)}."
    if len(frame.objects) == 1 and display_type(frame.objects[0]) in SCENE_PLAY_PLACES:
        place = display_type(frame.objects[0])
        return f"{subject} played {place_prep(place)} {renderer.obj(frame.objects[0])}."
    return f"{subject} played with {objects}." if objects else f"{subject} played happily."


@REGISTRY.renderer("friendship")
def render_friendship(renderer, frame):
    renderer.subj(frame.actor)
    party = renderer.participants(frame)
    if party and len(frame.meta.get("participants", [])) > 2:
        return f"{party} became good friends."
    if frame.actor and frame.patient:
        return f"{frame.actor.id} and {frame.patient.id} became good friends."
    return "They became good friends."


@REGISTRY.renderer("lesson")
def render_lesson(renderer, frame):
    subject = renderer.subj(frame.actor)
    concepts = renderer.concepts(frame)
    topic = join([c for c in concepts if c not in {"lesson", "moral", "learn"}])
    return f"{subject} learned an important lesson about {topic}." if topic else f"{subject} learned an important lesson."


@REGISTRY.renderer("reaction", "emotion")
def render_emotion(renderer, frame):
    subject = renderer.subj(frame.actor)
    concepts = renderer.concepts(frame)
    objects = renderer.objs(frame)
    if frame.kind == "reaction":
        if "cough" in concepts and "cover" in concepts:
            poss = frame.actor.pronoun("possessive") if frame.actor is not None else "their"
            return f"{subject} coughed and covered {poss} eyes."
        if "reprimand" in concepts:
            return f"{subject} was angry and scolded them."
    if "love" in concepts and objects:
        return f"{subject} loved {objects}."
    feeling = join([emotion_word(c) for c in concepts])
    party = renderer.participants(frame)
    if frame.kind == "emotion" and party and len(frame.meta.get("participants", [])) > 1:
        return f"{party} felt {feeling}." if feeling else f"{party} felt a lot of feelings."
    return f"{subject} felt {feeling}." if feeling else f"{subject} felt a lot of feelings."


@REGISTRY.renderer("encounter")
def render_encounter(renderer, frame):
    subject = renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    if frame.patient and frame.patient != frame.actor:
        suffix = f" and saw {objects}" if objects else ""
        return f"{subject} met {renderer.obj(frame.patient)}{suffix}."
    if objects:
        if any(display_type(o) in {"shadow", "noise"} for o in frame.objects):
            return f"{subject} noticed {objects}."
        return f"{subject} saw {objects}."
    return f"{subject} met {renderer.obj(frame.patient)}." if frame.patient else f"{subject} met someone."


@REGISTRY.renderer("visit")
def render_visit(renderer, frame):
    subject = renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    party = renderer.participants(frame)
    regular, positioned = renderer.split_position_objects(frame.objects)
    if positioned and regular:
        place = join([renderer.obj(o) for o in regular])
        where = join([renderer.obj(o) for o in positioned])
        group = party if party and len(frame.meta.get("participants", [])) > 1 else subject
        return f"{group} visited {place} and spent time {where}."
    if frame.patient and not frame.objects:
        return f"{subject} visited {renderer.obj(frame.patient)}."
    if party and len(frame.meta.get("participants", [])) > 1:
        return f"{party} visited {objects or renderer.obj(frame.patient)}."
    return f"{subject} visited {objects or renderer.obj(frame.patient)}."


@REGISTRY.renderer("problem")
def render_problem(renderer, frame):
    subject = renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    concepts = renderer.concepts(frame)
    if objects:
        object_names = [display_type(o) for o in frame.objects]
        if "noise" in object_names:
            return "A loud noise interrupted the moment."
        return f"There was a problem with {objects}."
    if concepts:
        return f"{subject} had a problem: {join(concepts)}."
    return f"{subject} had a problem."


@REGISTRY.renderer("transform")
def render_transform(renderer, frame):
    renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    target = phrase(frame.result, renderer.world)
    return f"{cap(objects or 'Something')} turned into {target}." if target else f"{cap(objects or 'Something')} changed."


@REGISTRY.renderer("give")
def render_give(renderer, frame):
    subject = renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    target = renderer.obj(frame.patient) if frame.patient else "someone"
    return f"{subject} gave {objects or 'something'} to {target}."


@REGISTRY.renderer("make")
def render_make(renderer, frame):
    subject = renderer.subj(frame.actor)
    if frame.source.lower() == "build" and frame.objects:
        thing = renderer.obj(frame.objects[0])
        if len(frame.objects) > 1:
            materials = join([renderer.obj(o) for o in frame.objects[1:]])
            return f"{subject} built {thing} with {materials}."
        return f"{subject} built {thing}."
    objects = renderer.objs(frame)
    return f"{subject} made {objects or 'something'}."


@REGISTRY.renderer("use")
def render_use(renderer, frame):
    subject = renderer.subj(frame.actor)
    if len(frame.objects) >= 2 and display_type(frame.objects[1]) in {"retrieve", "find", "fix", "clean"}:
        tool = renderer.obj(frame.objects[0])
        action = display_type(frame.objects[1])
        target = ""
        if frame.objects[1].traits:
            target = join([renderer.obj(renderer.world.physical(t)) for t in frame.objects[1].traits])
        verb = "look for" if action == "find" else action
        return f"{subject} used {tool} to {verb} {target}.".strip()
    objects = renderer.objs(frame)
    return f"{subject} used {objects or 'it'}."


@REGISTRY.renderer("show")
def render_show(renderer, frame):
    subject = renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    target = renderer.obj(frame.patient) if frame.patient else "everyone"
    return f"{subject} showed {objects or 'it'} to {target}."


@REGISTRY.renderer("calendar_add")
def render_calendar_add(renderer, frame):
    renderer.subj(frame.actor)
    party = renderer.participants(frame)
    event = next((o for o in frame.objects if display_type(o) != "calendar"), None)
    event_text = renderer.obj(event) if event is not None else "a special day"
    if party:
        return f"{party} added {event_text} to the calendar."
    return f"{renderer.subj(frame.actor)} added {event_text} to the calendar."


@REGISTRY.renderer("anticipation")
def render_anticipation(renderer, frame):
    subject = renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    party = renderer.participants(frame)
    if not objects:
        return ""
    topic = objects or "the special day"
    if party and len(frame.meta.get("participants", [])) > 1:
        return f"{party} looked forward to {topic}."
    return f"{subject} looked forward to {topic}."


@REGISTRY.renderer("celebration")
def render_celebration(renderer, frame):
    renderer.subj(frame.actor)
    party = renderer.participants(frame)
    if party:
        return f"{party} celebrated together."
    return "Everyone celebrated together."


@REGISTRY.renderer("receive")
def render_receive(renderer, frame):
    subject = renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    return f"{subject} received {objects or 'something'}."


@REGISTRY.renderer("return")
def render_return(renderer, frame):
    subject = renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    if len(frame.objects) == 1 and display_type(frame.objects[0]) == "play":
        return f"{subject} went back to playing."
    return f"{subject} returned {objects or 'home'}."


@REGISTRY.renderer("praise")
def render_praise(renderer, frame):
    subject = renderer.subj(frame.actor)
    if frame.patient:
        return f"{subject} praised {renderer.obj(frame.patient)}."
    if len(frame.objects) == 1 and display_type(frame.objects[0]) == "cool":
        return f"{subject} thought it was cool."
    objects = renderer.objs(frame)
    return f"{subject} praised {objects}." if objects else f"{subject} praised them."


@REGISTRY.renderer("advice")
def render_advice(renderer, frame):
    subject = renderer.subj(frame.actor)
    if frame.source.lower() == "suggest":
        if any(display_type(o) == "build" for o in frame.objects):
            return f"{subject} suggested building something."
        return f"{subject} made a suggestion."
    return f"{subject} gave helpful advice." if frame.actor else "There was helpful advice."


@REGISTRY.renderer("break", "broken")
def render_break(renderer, frame):
    renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    return f"{cap(objects or 'Something')} broke."


@REGISTRY.renderer("fix")
def render_fix(renderer, frame):
    subject = renderer.subj(frame.actor)
    objects = renderer.objs(frame)
    return f"{subject} fixed {objects or 'it'}."
