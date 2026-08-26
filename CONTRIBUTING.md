# Contribuir | Contributing

## Português

Obrigado pelo interesse no projeto. O modelo de manutenção institucional ainda
está a ser definido. Até existir uma decisão, Fábio Matias (`@SlicF`) mantém o
projeto e analisa as alterações propostas.

### Propor uma alteração

1. Crie um *fork* e uma branch dedicada à alteração.
2. Mantenha o commit focado e não inclua outputs gerados que não sejam
   necessários.
3. Execute, a partir de `src/`:

   ```bash
   python -m unittest discover -p "test_*.py" -v
   ```

4. Valide também o JavaScript, a partir da raiz:

   ```bash
   node --check docs/app.js
   ```

5. Abra um *pull request* e explique o problema, a solução e a validação
   realizada.

Para alterações à extração ou publicação de épocas, preserve a proteção contra
folhas semanticamente iguais descrita no README. Não inclua credenciais, dados
pessoais nem ficheiros locais de configuração.

Ao contribuir, aceita que a sua contribuição seja disponibilizada sob a
[licença MIT](LICENSE). Os dados importados das fontes oficiais da Taça UA não
são abrangidos automaticamente por essa licença.

## English

Thank you for your interest in the project. Its institutional maintenance model
is still being decided. Until a decision is made, Fábio Matias (`@SlicF`)
maintains the project and reviews proposed changes.

### Proposing a change

1. Create a fork and a branch dedicated to the change.
2. Keep the commit focused and exclude unrelated generated outputs.
3. From `src/`, run:

   ```bash
   python -m unittest discover -p "test_*.py" -v
   ```

4. From the repository root, also validate the JavaScript:

   ```bash
   node --check docs/app.js
   ```

5. Open a pull request explaining the problem, the solution, and the checks
   performed.

Changes to season extraction or publishing must preserve the protection against
semantically identical sheets documented in the README. Do not submit secrets,
personal data, or local configuration files.

By contributing, you agree that your contribution may be distributed under the
[MIT License](LICENSE). Data imported from official Taça UA sources is not
automatically covered by that license.
