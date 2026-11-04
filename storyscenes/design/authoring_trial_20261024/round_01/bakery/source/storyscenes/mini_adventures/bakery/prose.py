"""Authored encounters; only committed state selects prose and callbacks."""


def render(scene, before, after):
    if scene == "launch":
        return ('Nell hid a paper crown under the village bakery counter. Tomorrow Mr Vale '
                'was retiring to the sea; tonight the village would surprise him with supper. '
                'Their plaited loaf waited in its tin. The windowless oven-room bulb had failed; '
                'the baker was fetching another from town. '
                '"His lantern," Kit suggested. "Ask without telling," Nell said. "Seven o\'clock. Not a word."')
    if scene == "borrow":
        return ('They crossed the lane to the workshop. "Could we borrow your lantern? Our bulb\'s gone," '
                'Nell asked. Vale lifted it off its hook. "Bring it back before I lock up. I need it '
                'for the cellar steps." Nell took the folded handle. Back across the lane, Kit held '
                'the bakery door for her and the borrowed light.')
    if scene == "glove":
        return ('A customer had left a green wool glove by the till. Kit tried it on; the empty '
                'fingers dangled beyond his own. "I could carry five more fingers in here." Nell '
                'laughed and pinned it to the noticeboard. "Leave some room for the owner." Kit '
                'tucked its thumb into its palm, making it wave at tomorrow\'s customers.')
    if scene == "darn":
        return ('They unfolded the supper cloth. A blue darn crossed one corner. Nell turned it '
                'toward the wall, but Kit turned it back. "He fixes things. He won\'t mind a mend." '
                'She smoothed the corner beside the head chair. The blue stitches looked almost '
                'like a small ladder, going nowhere in particular. She left them showing.')
    if scene == "crown":
        return ('Nell retrieved the crown and read VALE aloud. "He knows his name," Kit said. '
                '"It\'s on all his parcels." She turned the paper over and wrote THANK YOU on '
                'the other side. Kit held it against the empty head chair. "Better." Nell put '
                'it back under the counter before anyone could look through the window.')
    if scene == "refill":
        return ('The lantern was still cold. Kit found a little bottle of lamp oil behind the '
                'till. Nell unscrewed the reservoir and poured in the last of it, keeping the '
                'spout against the rim. "That was all," Kit said, tipping the empty bottle. '
                'She tightened the cap. "Then we\'ll have to make it last."')
    if scene == "inspect_wick":
        detail = ('It refused to turn. "We\'ll have to ease that before lighting it," Nell said.'
                  if before["lantern.wick_stuck"] else
                  'It turned smoothly, lifting a little black edge. "That works," Nell said.')
        return ('Kit pointed to the lantern\'s brass wheel. "Is that the light?" Nell tried it '
                'while the glass was cold. ' + detail +
                ' Kit put his hands in his pockets. "I thought you just asked it nicely." '
                '"You can try that with the oven."')
    if scene == "window_note":
        return ('Kit read the little supper notice propped in the window. "Not a word, you said." '
                'Nell snatched it down and slid a bread-price card in front of it. Across the '
                'lane the workshop window reflected the sky; she could not tell whether Vale '
                'had looked. "We are extremely good at secrets," Kit whispered to the price card.')
    if scene == "mend_crown":
        return ('One tooth of the paper crown hung by a thread. Kit found a clean paper strip; '
                'Nell pasted it behind the tear and held the edges together. "Don\'t breathe on '
                'the king," she said. Kit held his breath until she laughed. The tooth stood '
                'upright again, with a pale seam running down its back.')
    if scene == "bake":
        if before["lantern.wick_stuck"]:
            wheel = ('As she had found, the wheel stuck.' if before["nell.knows_wick"] else
                     'The wheel stuck when Nell tried it.')
            wheel += ' She eased the bent guard aside; it turned.'
        else:
            wheel = 'Nell turned the wheel; the wick rose.'
        return ('They carried the lantern into the oven room. ' + wheel +
                ' She lit it and set it on the stone shelf, clear of the towels. Kit helped '
                'slide the loaf into the oven. "Everybody\'s bread," he said. Nell closed the '
                'door gently. For ten minutes the plaits swelled in the heat.')
    if scene == "knock":
        demand = ('"The van\'s early. I need my lantern now," Vale said.' if before["vale.early_van"] else
                  '"Nearly locking-up time. May I have my lantern?" Vale asked.')
        return ('A knock reached them from the bakery. Nell extinguished the lantern and carried '
                'it out to answer. ' + demand +
                ' Behind Nell, the oven ticked. The loaf needed ten more minutes, and she needed '
                'light to check it. Kit looked at her, then at the crown hidden beneath the counter.')
    if scene == "confess":
        return ('"There\'s a loaf for your leaving supper," Nell said. "It was meant to be a surprise." '
                'Vale took off his cap. Kit stopped hiding the crown. "Could you stay and help?" '
                'Nell asked. Vale set his key beside the till. "The cellar can wait ten minutes. '
                'Let\'s see what your loaf needs." The secret was out.')
    if scene == "request_extension":
        if before["vale.early_van"]:
            return ('"Ten more minutes?" Nell asked, keeping her body between Vale and the crown. '
                    'He shook his head. "The van won\'t wait while I empty the cellar." She gave '
                    'him the lantern. He crossed back to the workshop with it. Kit listened to '
                    'the oven ticking. "He still doesn\'t know." Nell wished that felt better.')
        return ('"Could we have ten more minutes?" Nell asked. "Then I\'ll bring it straight over." '
                'Vale checked his watch. "Ten. I can pack the counter first." He went back '
                'across the lane, leaving the lantern in her hand. Kit let out his breath. '
                'Nell held up both hands, counting the minutes on her fingers.')
    if scene == "return_now":
        return ('Nell folded down the handle and gave the lantern back. "Thank you. We\'ll manage." '
                'Vale carried it across to his workshop. Kit watched the light disappear through '
                'the door. "What about the loaf?" Nell looked toward the oven room. Its doorway '
                'was dark again. "We won\'t guess when everybody has put work into it."')
    if scene in ("finish_secret", "finish_together"):
        start = ('Vale followed them into the oven room. Nell gave him the lantern; he held it '
                 'while she relit it.' if scene == "finish_together" else
                 'They carried the lantern back into the oven room and relit it. Kit watched the clock.')
        return (start + ' After ten minutes Nell opened the oven and tapped the loaf: hollow. '
                'Together they lifted it onto the rack, turned the oven off, and extinguished '
                'the light. Once the loaf cooled, Kit carried it out to the supper table.')
    if scene == "postpone":
        reason = ('Nell tried the lantern again; its dry wick would not catch.' if after["lantern.relight_failed"] else
                  'The borrowed light was no longer theirs to use.')
        return (reason + ' Nell went into the oven room and turned the oven off without opening '
                'it. The baker would finish the loaf when he returned with a bulb. Back at '
                'the counter she wrote: Breakfast here before you go? "Tell him it\'s from both '
                'of us," Kit said.')
    if scene == "ending_secret":
        detail = ' The blue darn lay beside his plate.' if before["cloth.darn_visible"] else ''
        return ('They took the lantern across the lane and invited Vale back. At the bakery '
                'door Nell stepped aside: the loaf stood on the supper table. "For me?" He '
                'forgot to take his cap off until Kit offered the crown.' + detail +
                ' He held his own dark lantern between his knees while Kit broke the first heel.')
    if scene == "ending_together":
        detail = ' He rested his wrist beside the blue darn.' if before["cloth.darn_visible"] else ''
        return ('Vale kept his lantern hooked over his wrist. There would be no shout of surprise '
                'when the others arrived; he was already cutting the heel. "Sorry you found '
                'out," she said. "I was going to eat standing up." He gave her half.' + detail +
                ' Kit placed the crown beside the bread, leaving flour on the dark lantern handle.')
    if scene == "ending_postponed":
        trip = ('They crossed to the workshop with the invitation, then came back to the bakery.'
                if before["vale.location"] == "workshop" else
                'Nell gave Vale the invitation beside the bakery counter.')
        return (trip + ' The lantern was back with its owner. "Before you leave," Nell had written '
                'under Breakfast. Kit set two cups beside the bread rack. The loaf was still '
                'unfinished inside; on the counter the crown waited upside down, keeping a place '
                'for a morning they had not had yet.')
    raise ValueError(scene)
