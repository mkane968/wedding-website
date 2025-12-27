describe("Chapel visual regression", () => {
    it("matches the provided sanctuary reference photo", () => {
        cy.visit("/chapel/");
        cy.wait(3000);
        cy.matchImageSnapshot("chapel-reference");
    });
});
