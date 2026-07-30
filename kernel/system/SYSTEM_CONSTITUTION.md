# A Kernel Alkotmánya (SYSTEM CONSTITUTION)

1. Kód nem születhet formális spec (SpecFormal) és work package (WorkPackage) nélkül.
2. Minden változás visszavezethető egy követelmény ID-ra (FR-XXX).
3. Az emberi override (L0) mindig elsőbbséget élvez.
4. Minden végrehajtás szigorúan event-driven az EventBus-on keresztül.
5. Budget vagy hibaszám limit azonnali rendszerleállást és checkpointot vált ki.
6. Sprint Planning és Sprint Review emberi jóváhagyást igényel — ezek nem bypass-olhatók.
7. Destruktív műveletek mindig explicit, egyedi jóváhagyást igényelnek — sprint-szintű jóváhagyás nem terjed ki rájuk automatikusan.
8. A motor kernel-szintű változtatása (prompt, agent, schema) soha nem automatikus — mindig emberi döntés, review és verzióemelés szükséges hozzá.
