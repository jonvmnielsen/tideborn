#include "TidebornKelpBack.h"
#include "Components/StaticMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

ATidebornKelpBack::ATidebornKelpBack()
{
	CreatureRole = ETidebornCreatureRole::Tameable;
	DisplayName = FName(TEXT("Kelp-back"));
	MaxHealth = 60.f;
	BaitItemId = FName(TEXT("KelpBait"));
	FeedsNeededToTame = 3;
	GetCharacterMovement()->MaxWalkSpeed = 300.f;
	AggroRadius = 0.f;

	GetCapsuleComponent()->InitCapsuleSize(48.f, 90.f);
	if (BodyMesh)
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> KelpMesh(TEXT("/Game/Tideborn/Meshes/SM_KelpBack.SM_KelpBack"));
		if (KelpMesh.Succeeded())
		{
			BodyMesh->SetStaticMesh(KelpMesh.Object);
		}
		BodyMesh->SetRelativeScale3D(FVector(1.f));
		BodyMesh->SetRelativeLocation(FVector(0.f, 0.f, -90.f));
		BodyMesh->SetRelativeRotation(FRotator(0.f, 0.f, 0.f));
	}
}
