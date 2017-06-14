var ChangeVariable = function(event)
{
        %SET{'org' value='{{organization(org.id)}}'}%
}

document.addEventListener('DOMContentLoaded', () => {
    document
        .querySelectorAll('.items-list')
        .forEach((el) => {
            el.addEventListener('click', ChangeVariable, true);
        });
}, false);
