#include "TidebornBurrHound.h"
#include "Components/StaticMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

ATidebornBurrHound::ATidebornBurrHound()
{
	CreatureRole = ETidebornCreatureRole::Threat;
	DisplayName = FName(TEXT("Burr-hound"));
	MaxHealth = 40.f;
	AggroRadius = 1000.f;
	AttackRange = 130.f;
	AttackDamage = 10.f;
	GetCharacterMovement()->MaxWalkSpeed = 460.f;

	GetCapsuleComponent()->InitCapsuleSize(55.f, 55.f);
	if (BodyMesh)
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> HoundMesh(TEXT("/Game/Tideborn/Meshes/SM_BurrHound.SM_BurrHound"));
		if (HoundMesh.Succeeded())
		{
			BodyMesh->SetStaticMesh(HoundMesh.Object);
		}
		BodyMesh->SetRelativeScale3D(FVector(1.f));
		BodyMesh->SetRelativeLocation(FVector(0.f, 0.f, -55.f));
		BodyMesh->SetRelativeRotation(FRotator(0.f, -90.f, 0.f));
	}
}
