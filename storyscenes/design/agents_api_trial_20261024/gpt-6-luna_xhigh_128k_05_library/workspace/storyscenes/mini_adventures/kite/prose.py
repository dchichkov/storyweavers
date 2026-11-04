'''Scene-sized prose conditioned on committed local-play outcomes.'''


def render(scene_id, p, before, after):
    if scene_id == 'promise':
        return (
            'Lio wanted to collect his reserved comic, but Nia was close to tears. '
            'The Moon in My Pocket had gone missing, and the library closed at six. '
            '“I’ll find it before closing,” he promised. Ms Vale lent him the book trolley. '
            'They used it to clear returned books from the aisle, then turned toward the shelves together.'
        )
    if scene_id == 'catalog':
        if after['catalog.lead'] == before['book.actual_spot']:
            return (
                'At the catalogue screen, Lio typed the title while Nia watched. '
                'This entry was current: it pointed to the place the book had actually been moved. '
                '“That’s better than guessing,” Nia said. Lio wrote the shelf location on their list, '
                'and the closing clock gave them one more reason to move steadily.'
            )
        return (
            'The catalogue still listed the animal-story shelf, but its date was old. '
            '“It may be wrong,” Nia said. Lio wrote down the low shelf anyway; an old location '
            'was a lead, not a promise. If the book was somewhere else, they would need another clue '
            'before the closing bell made the search impossible.'
        )
    if scene_id == 'librarian':
        if before['book.found']:
            return (
                'Lio brought Ms Vale the news and the list of places they had checked. '
                'She was glad the book was safe, and confirmed that the trolley belonged back in its bay. '
                'Nia kept one hand on the cover. For once, Lio did not try to hurry her through the explanation; '
                'the search had ended, but their borrowed things still needed returning.'
            )
        if before['library.closed'] or not p.staff_available:
            return (
                'At the desk, no librarian was free to check the reshelving notes. '
                'Lio left the title where staff could see it, but no new location appeared. '
                'Nia looked at the list instead of blaming him. The trolley was still useful, '
                'though a high shelf would stay out of reach unless a staff member and a safe ladder were available.'
            )
        if p.ladder_stable:
            return (
                'Ms Vale checked the reshelving note and told them the most likely spot. '
                'The ladder’s feet sat evenly on the floor, so she offered to hold it if the title was high. '
                '“I’ll guide you,” she said. Nia added the clue to the list; no one had to guess or climb alone.'
            )
        return (
            'Ms Vale checked the reshelving note and found a useful location clue. '
            'Then she tested the step ladder and shook her head: one foot rocked on the uneven floor. '
            '“Not safe today,” she said. Lio thanked her. The clue could still guide a shelf search, '
            'but nobody would risk a fall to keep a promise.'
        )
    if scene_id == 'returns_search':
        noise = 'The left wheel squeaked, costing them a little time.' if not p.trolley_wheel_ok else 'The trolley rolled quietly beside them.'
        if after['book.found']:
            return (
                f'{noise} Lio sorted the returns instead of shaking the stack. Nia read the titles aloud, '
                'and there, between two picture books, sat the silver moon cover. He moved it onto the trolley '
                'without bending the pages. The cart had cleared their aisle and carried the very book they had promised to find.'
            )
        ending = 'The closing bell sounded while they checked the last book.' if after['library.closed'] else 'The title was not among the returns.'
        return (
            f'{noise} Lio lifted each return carefully, while Nia checked the covers. {ending} '
            'They left the books in a neat stack instead of scattering them. The trolley had helped them sort, '
            'but it had not yet brought the missing moon any closer.'
        )
    if scene_id == 'low_search':
        if after['book.found']:
            return (
                'Nia followed the picture labels while Lio checked the low shelf. Behind a book about foxes, '
                'the silver moon peeked out. He lifted The Moon in My Pocket free and set it on the trolley. '
                '“You saw the right place,” he said. Nia smiled at the shelf, not at the clock.'
            )
        ending = 'The bell rang before they could try another shelf.' if after['library.closed'] else 'No silver moon waited there.'
        helper = 'Nia read the picture labels with him.' if before['friend.shelf_skill'] else 'Lio checked the shelf one book at a time.'
        return (
            f'{helper} The catalogue’s low-shelf lead brought them to the animal stories. {ending} '
            'They returned each book to its place. The wrong location cost a minute, but neither child '
            'pretended that an empty shelf was a discovery.'
        )
    if scene_id == 'ladder_search':
        if after['book.found']:
            return (
                'With Ms Vale holding the stable ladder, Lio reached only where she pointed. '
                'Behind the atlases he saw a silver moon and drew the book toward him. '
                'Nia recognized the crease on its cover. He placed it on the trolley, and Ms Vale '
                'made sure both children were safely back on the floor.'
            )
        return (
            'Ms Vale steadied the ladder as Lio checked the high shelf she had named. '
            'The title was not there. When the closing bell sounded, she asked him to climb down at once. '
            'He did. The search had taken time, but nobody turned a library ladder into a dare.'
        )
    if scene_id == 'bookmark_vignette':
        return (
            'Nia unfolded a blue paper bookmark with a silver moon she had drawn herself. '
            '“I made it for that book,” she said, letting Lio hold it. He traced the tiny moon in the air, '
            'careful not to crease the paper. It did not tell them where the book was, but it made their search '
            'feel like Nia’s story too.'
        )
    if scene_id == 'window_vignette':
        if before['book.found']:
            return (
                'With the book already safe on the trolley, Nia told Lio why she liked the window seat: '
                'the pictures looked brighter there. He listened instead of checking the clock. '
                'They had found what they came for, and the quiet corner gave Nia room to be glad '
                'without turning her relief into another instruction.'
            )
        if after['book.found']:
            return (
                'Nia lifted the window-seat cushion and spotted the silver moon underneath. '
                'The book had been tucked into the gap, its cover turned toward the wall. '
                'Lio moved it to the trolley. “I knew I read here,” Nia said. '
                'She had remembered a place that his list could never have guessed.'
            )
        if after['library.closed']:
            return (
                'They checked the window seat just as the closing bell sounded, but the cushion was empty. '
                'Nia remembered reading there and admitted she had carried the book away afterward. '
                'Lio closed the list. They had reached the end of the time they were allowed, '
                'not the end of caring about one another.'
            )
        return (
            'Nia lifted the window-seat cushion and checked the gap where a book might slide. '
            'Nothing with a silver moon was there. She remembered sitting in that spot, but also carrying '
            'the book away. Lio marked the seat checked. A memory was useful, even when it was not the answer.'
        )
    if scene_id == 'friend_vignette':
        return (
            'Nia took the search list from Lio. “I can remember things, not just wait for you,” she said. '
            'He started to apologize, then stopped and handed her the pencil instead. '
            'She chose the next place to check. The list was still only paper, but sharing it changed '
            'who was making the decisions.'
        )
    if scene_id == 'shelf_vignette':
        if after['book.found']:
            return (
                'Nia showed Lio the little picture labels on the spines. They used them to straighten a few '
                'books that had been turned sideways, leaving the trolley easier for Ms Vale to sort. '
                '“The pictures are a map,” Nia said. Lio had been looking for a map on a screen; '
                'he had missed the one she already knew how to read.'
            )
        return (
            'Nia explained how the tiny pictures on the spines marked different shelves. '
            'Lio had been staring at words and dates; she knew the pictures. She pointed to the animal label '
            'and showed him how to follow it without pulling every book out. Her knowledge gave them '
            'another careful way to search.'
        )
    if scene_id == 'ending_found':
        bookmark = 'Nia slid her moon bookmark between the pages.' if before['friend.bookmark_vignette'] else 'Nia held the book close.'
        return (
            f'Lio handed The Moon in My Pocket to Nia. {bookmark} '
            'They returned the useful trolley to its bay, with the other books still neatly sorted. '
            'His reserved comic had gone back onto the shelf, and he felt disappointed. Nia asked him to hear '
            'her favorite page. The promise was kept; the cost of it was real, and so was the friendship.'
        )
    if scene_id == 'ending_miss':
        bookmark = 'He returned her bookmark to her pocket.' if before['friend.bookmark_vignette'] else 'Nia kept her hands in her pockets.'
        return (
            f'Lio told Nia the truth: they had not found her book. {bookmark} '
            'She chose The Cloud Garden instead, and he returned the useful trolley to its bay. '
            '“I’m still disappointed,” she said. “I know,” Lio answered. They left with a different story '
            'to read, and without pretending the missing one had been found.'
        )
    raise ValueError(f'No prose for scene: {scene_id}')
