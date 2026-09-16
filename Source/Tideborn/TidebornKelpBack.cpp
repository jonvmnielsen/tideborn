#include "TidebornKelpBack.h"
#include "GameFramework/CharacterMovementComponent.h"

ATidebornKelpBack::ATidebornKelpBack()
{
	CreatureRole = ETidebornCreatureRole::Tameable;
	DisplayName = FName(TEXT("Kelp-back"));
	MaxHealth = 60.f;
	BaitItemId = FName(TEXT("KelpBait"));
	FeedsNeededToTame = 3;
	BodyColor = FLinearColor(0.15f, 0.45f, 0.55f);
	GetCharacterMovement()->MaxWalkSpeed = 300.f;
	AggroRadius = 0.f;
}

