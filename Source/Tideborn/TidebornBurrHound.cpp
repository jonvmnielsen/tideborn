#include "TidebornBurrHound.h"
#include "GameFramework/CharacterMovementComponent.h"

ATidebornBurrHound::ATidebornBurrHound()
{
	CreatureRole = ETidebornCreatureRole::Threat;
	DisplayName = FName(TEXT("Burr-hound"));
	MaxHealth = 40.f;
	AggroRadius = 1000.f;
	AttackRange = 130.f;
	AttackDamage = 10.f;
	BodyColor = FLinearColor(0.55f, 0.2f, 0.15f);
	GetCharacterMovement()->MaxWalkSpeed = 460.f;
}

