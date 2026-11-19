filtres
    détection de visage
        en seconde étape, reconnaissance à partir de photos deja prises
    localsiation
        Use a geocoding service/library to map coords to a named location (city/neighborhood) ("paris trip")
app
    détection de doublons meme si nom ou infos différentes
    avoir une notion de source (images deja triées pour reconnaissance faiclae notamment) et d'inputs (images àt rier)
cicd
    avoir un résultat type attendu en sortie basé sur les samples et le mettre en tant que test E2E dans pipeline
        utilsier "jq" pour ca ?
    dependabot sur les dépendances
    mettre dans un cache les différents execs durant builds si pas de changement
    supporter ubuntu build en cicd