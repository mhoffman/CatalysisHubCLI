#!/usr/bin/python


def extract_atoms(molecule):
    # return a string with all atoms in molecule
    if molecule == '':
        return molecule
    try:
        return float(molecule)
    except:
        pass
    atoms = ''
    if not molecule[0].isalpha():
        i = 0
        while not molecule[i].isalpha():
            i += 1
        prefactor = float(molecule[:i])
        if prefactor < 0:
            prefactor = abs(prefactor)
            sign = '-'
        else:
            sign = ''
        molecule = molecule[i:]
    else:
        prefactor = 1
        sign = ''
    for k in range(len(molecule)):
        if molecule[k].isdigit():
            for j in range(int(molecule[k]) - 1):
                atoms += molecule[k - 1]
        else:
            atoms += molecule[k]
    if prefactor % 1 == 0:
        atoms *= int(prefactor)
    elif prefactor % 1 == 0.5:
        atoms_sort = sorted(atoms)
        N = len(atoms)
        atoms = ''
        for n in range(N):
            for m in range(int(prefactor - 0.5)):
                atoms += atoms_sort[n]
            if n % 2 == 0:
                atoms += atoms_sort[n]

    return sign + ''.join(sorted(atoms))

def add_atoms(atoms_list):
    add = ''
    sub = ''
    for atoms in atoms_list:
        if isinstance(atoms, float):
            continue
        if len(atoms)>0 and atoms[0] == '-':
            sub += atoms[1:]
        else:
            add += atoms
    return add.replace(sub, '', 1)

def check_reaction(reactants, products):
    """
    check the stoichiometry and format of chemical reaction used for 
    folder structure.
    list of reactants -> list of products
    """
    reactants = [reactant.strip('star').strip('gas') for reactant in reactants]
    products = [product.strip('star').strip('gas') for product in products]

    reactant_atoms = [extract_atoms(reactant) for reactant in reactants]
    product_atoms = [extract_atoms(product) for product in products]

    reactants = add_atoms(reactant_atoms)
    products = add_atoms(product_atoms)

    r_stars = 0
    p_stars = 0
    for i, a in enumerate(reactant_atoms):
        if a=='' or 'star' in reactants[i]:
            r_stars += 1
        elif isinstance(a, float):
            r_stars += a
    for a in product_atoms:
        if a=='':
            p_stars += 1
        elif isinstance(a, float):
            p_stars += a
    print r_stars, p_stars
    assert ''.join(sorted(reactants)) == ''.join(sorted(products))
    #assert r_stars == p_stars, 'Please match the number of surfaces on each side. Left side: {} *s, right side: {} *s'.format(r_stars, p_stars)
